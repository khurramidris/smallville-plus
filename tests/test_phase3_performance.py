import asyncio
import json
from decimal import Decimal

import pytest

from smallville.agents.mind import Mind
from smallville.apps.phone import CreateEvent, SendMessage
from smallville.config import Config
from smallville.engine.scheduler import Scheduled
from smallville.engine.simulation import Simulation
from smallville.llm.gateway import BudgetExceeded, Completion, Gateway
from smallville.llm.mock import MockLLM
from smallville.world.models import DailyPlan, Intent, change
from smallville.world.store import replay
from tests.test_llm import call, paid_config
from tests.test_phase3_economy import economic_world as economic_world


class OverlappingProvider:
    def __init__(self):
        self.active = self.maximum = self.calls = 0
        self.entered = asyncio.Event()
        self.release = asyncio.Event()

    async def complete(self, **kwargs):
        self.calls += 1
        self.active += 1
        self.maximum = max(self.maximum, self.active)
        self.entered.set()
        try:
            await self.release.wait()
            return Completion('{"ok":true}', 10, 5)
        finally:
            self.active -= 1


async def test_independent_requests_overlap_but_duplicate_prompts_are_cached(tmp_path):
    config = paid_config("1").model_copy(update={"decision_concurrency": 2})
    provider = OverlappingProvider()
    gateway = Gateway(tmp_path, config, provider)
    tasks = [asyncio.create_task(call(gateway, {"task": str(i)})) for i in range(4)]
    try:
        await provider.entered.wait()
        for _ in range(20):
            await asyncio.sleep(0)
        assert provider.active == provider.maximum == 2
        provider.release.set()
        await asyncio.gather(*tasks)
        before = provider.calls
        await asyncio.gather(*[call(gateway, {"task": "identical"}) for _ in range(5)])
        assert provider.calls == before + 1
        assert gateway.summary()["cache_hits"] == 4
        timing = gateway.timing_summary()
        assert timing["timed_calls"] == timing["provider_calls"] == 5
        assert timing["provider_ms_mean"] > 0
        assert timing["queue_ms_sum"] >= 0
    finally:
        provider.release.set()
        await asyncio.gather(*tasks, return_exceptions=True)
        gateway.close()


async def test_concurrent_budget_counts_inflight_reservations_and_cancellation(tmp_path):
    config = paid_config("0.00124").model_copy(update={"decision_concurrency": 2})
    provider = OverlappingProvider()
    gateway = Gateway(tmp_path, config, provider)
    first = asyncio.create_task(call(gateway, {"task": "first"}))
    try:
        await provider.entered.wait()
        with pytest.raises(BudgetExceeded):
            await call(gateway, {"task": "second"})
        assert provider.calls == 1
        reserved = gateway.spent
        assert Decimal(0) < reserved <= config.max_usd
        first.cancel()
        with pytest.raises(asyncio.CancelledError):
            await first
        assert gateway.spent == reserved
        assert gateway.summary()["uncertain_calls"] == 1
        assert provider.active == 0
    finally:
        first.cancel()
        await asyncio.gather(first, return_exceptions=True)
        gateway.close()


class YieldingMock(MockLLM):
    def __init__(self):
        super().__init__()
        self.active = self.maximum = 0

    async def complete(self, **kwargs):
        self.active += 1
        self.maximum = max(self.maximum, self.active)
        try:
            # Deliberately yield so the test would fail with the old gateway lock.
            await asyncio.sleep(0.001)
            return await super().complete(**kwargs)
        finally:
            self.active -= 1


async def test_parallel_scene_has_private_calls_ordered_intents_and_exact_replay(tmp_path):
    config = Config(phase=3, decision_concurrency=4, routine_actions=True, compact_context=True)
    sim = Simulation(tmp_path / "original", config, cache_path=tmp_path / "shared.sqlite3")
    provider = YieldingMock()
    sim.gateway.backend = provider
    try:
        result = await sim.run(0.375)
        assert result["status"] == "completed"
        assert 1 < provider.maximum <= 4
        assert provider.active == 0
        snapshot = sim.world.snapshot()
        for event in sim.world.log.read(limit=10000):
            if event.kind == "llm_call":
                assert event.actor in {a.id for a in sim.world.agents()}
                assert "provider_ms" not in event.data
        restored = replay(sim.world.log.path, tmp_path / "restored")
        try:
            assert restored.snapshot() == snapshot
            assert restored.log.path.read_bytes() == sim.world.log.path.read_bytes()
        finally:
            restored.close()
    finally:
        sim.close()
    cached = Simulation(
        tmp_path / "cached",
        config.model_copy(update={"replay_only": True}),
        cache_path=tmp_path / "shared.sqlite3",
    )
    try:
        result = await cached.run(0.375)
        assert result["status"] == "completed"
        assert result["cost"]["cache_hits"] == result["cost"]["calls"] > 0
        actual = cached.world.snapshot()
        for row in actual["metadata"]:
            if "replay_only" in row:
                row["replay_only"] = False
        assert actual == snapshot
    finally:
        cached.close()


async def test_chosen_routine_stops_for_phone_calendar_needs_and_work_limit(economic_world, town):
    world, base, gm, gateway = economic_world
    config = base.model_copy(update={"routine_actions": True, "compact_context": True})
    mind = Mind(world, town, gateway, config)
    actor = world.agent("john_lin")
    actor.location = actor.persona.workplace
    actor.needs.fullness = actor.needs.energy = 90
    actor.plan = DailyPlan(
        day=0,
        blocks=[
            {"start": 0, "end": 540, "activity": "sleep", "location": actor.persona.home},
            {"start": 540, "end": 1020, "activity": "work", "location": actor.persona.workplace},
            {"start": 1020, "end": 1440, "activity": "leisure", "location": actor.persona.home},
        ],
    )
    intent = Intent(kind="work", text="I will keep working.", duration=30)
    world.log.append(
        600,
        "chosen_routine",
        changes=[
            change("agents", actor.id, actor),
            mind.routine_change(actor, intent, 600),
        ],
    )
    continuation = mind.continue_routine(actor, 630)
    assert continuation.kind == "work" and continuation.duration == 60
    assert gateway.summary()["calls"] == 0
    assert mind.continue_routine(actor, 720) is None
    actor.needs.fullness = 20
    assert mind.continue_routine(actor, 630) is None
    actor.needs.fullness = 90
    job = world.get("jobs", actor.id)
    job["worked_minutes"]["0"] = job["max_daily_minutes"] - 10
    world.log.append(600, "worked", changes=[change("jobs", actor.id, job)])
    assert mind.continue_routine(actor, 630).duration == 10
    job["worked_minutes"]["0"] = 0
    world.log.append(600, "reset_work", changes=[change("jobs", actor.id, job)])
    appointment = CreateEvent(title="Check in", start=645, end=660, location=actor.location)
    world.log.append(
        600, "appointment", changes=gm.calendar.create_changes(actor, appointment, 600)
    )
    assert mind.continue_routine(actor, 630).duration == 15
    sender = world.agent("mei_lin")
    _, updates = gm.messaging.delivery_changes(
        sender, SendMessage(to=actor.id, body="Please call me."), 620
    )
    world.log.append(620, "phone", changes=updates)
    gm.messaging.read_changes(actor, 630)
    assert actor.surprise
    assert mind.continue_routine(actor, 630) is None


async def test_cancellation_settles_every_parallel_request_before_run_finishes(tmp_path):
    sim = Simulation(tmp_path, Config(phase=3, decision_concurrency=4))
    provider = OverlappingProvider()
    sim.gateway.backend = provider
    running = asyncio.create_task(sim.run(1))
    try:
        await provider.entered.wait()
        for _ in range(10):
            await asyncio.sleep(0)
        running.cancel()
        result = await running
        assert result["status"] == "interrupted"
        assert provider.active == 0
        assert result["cost"]["uncertain_calls"] >= 1
        assert not sim.gateway.ledger.execute(
            "SELECT 1 FROM calls WHERE status='reserved'"
        ).fetchone()
        events = sim.world.log.read(limit=10000)
        assert events[-1].kind == "run_finished"
        assert sum(e.kind == "llm_call" for e in events) == result["cost"]["calls"]
    finally:
        running.cancel()
        await asyncio.gather(running, return_exceptions=True)
        sim.close()


def test_compact_context_limits_history_without_remote_stock(economic_world, town):
    world, base, gm, gateway = economic_world
    mind = Mind(world, town, gateway, base.model_copy(update={"compact_context": True}))
    actor = world.agent("john_lin")
    context = mind.context(actor, 600, "action")
    assert len(context["sent"]) <= 8 and len(context["calendar"]) <= 12
    assert "work_minutes_available" in context
    assert all(
        town.locations[i].is_open(600 + town.travel_minutes(actor.location, i))
        for i in context["reachable_now"]
    )
    assert "provider_ms" not in json.dumps(context)


async def test_same_scene_decisions_commit_in_order_and_gm_reserves_capacity(tmp_path):
    sim = Simulation(tmp_path, Config(phase=3, decision_concurrency=4))
    identifiers = ["john_lin", "mei_lin"]
    seen = []
    try:
        updates = []
        for identifier in identifiers:
            actor = sim.world.agent(identifier)
            actor.pending, actor.busy_until, actor.activity = None, 600, "wait"
            updates.append(change("agents", identifier, actor))
        cafe = sim.world.location("hobbs_cafe")
        cafe.capacity = 1
        updates.append(change("locations", cafe.id, cafe))
        sim.world.log.append(600, "scene", changes=updates)
        sim.clock.advance(600)

        async def decide(actor, minute):
            if actor.id == identifiers[0]:
                await asyncio.sleep(0.005)
            seen.append(sim.world.agent(identifiers[0]).location)
            return Intent(kind="move", text="I want coffee.", target=cafe.id)

        sim.mind.decide = decide
        await sim._wake_batch(
            [Scheduled(600, 10, i, "wake", a) for i, a in enumerate(identifiers)], 1440
        )
        home = sim.world.agent(identifiers[1]).persona.home
        assert seen == [home, home]
        events = sim.world.log.read(limit=10000)
        assert [e.actor for e in events if e.kind == "intention"] == identifiers
        outcomes = [e for e in events if e.kind in ("action_started", "action_rejected")]
        assert [(e.actor, e.kind) for e in outcomes] == [
            (identifiers[0], "action_started"),
            (identifiers[1], "action_rejected"),
        ]
        assert "space" in outcomes[-1].data["reason"]
    finally:
        sim.close()
