from __future__ import annotations

import asyncio
import math
from contextvars import ContextVar
from pathlib import Path

from smallville.agents.drives import advance_drives
from smallville.agents.goals import initial_goal_changes
from smallville.agents.knowledge import campaign_knowledge_change
from smallville.agents.mind import Mind
from smallville.apps.civic import Council, NoticeBoard, initial_council
from smallville.apps.gatherings import initial_gathering
from smallville.config import Config
from smallville.economy.system import Economy, initial_economy
from smallville.engine.clock import SimClock
from smallville.engine.scheduler import EventBus, Scheduler
from smallville.gm.master import GameMaster
from smallville.llm.gateway import BudgetExceeded, Gateway, LiteLLMBackend, ModelFailure
from smallville.llm.mock import MockLLM, routine
from smallville.personas.population import Population
from smallville.personas.seeds import load_agents
from smallville.world.maps import MapProvider, SmallvilleMap
from smallville.world.models import Intent, change
from smallville.world.store import WorldState


def bootstrap(
    world: WorldState, town: MapProvider, config: Config, population: Population | None = None
):
    if world.log.read(limit=1):
        raise ValueError("run directory already contains a simulation; choose a fresh directory")
    if population:
        population.validate_map(town)
        agents = [a.model_copy(deep=True) for a in population.agents]
    else:
        agents = load_agents(town, config.seed)
    changes = [change("locations", loc.id, loc) for loc in town.locations.values()]
    for agent in agents:
        # Begin at midnight in bed; no inference during this known sleep period.
        plan = routine(
            {
                "self": {
                    "id": agent.id,
                    "home": agent.persona.home,
                    "workplace": agent.persona.workplace,
                },
                "minute": 0,
                "work_status": agent.persona.facts.get("work_status", ""),
            }
        )
        wake = plan["blocks"][0]["end"]
        agent.busy_until = wake
        agent.pending = {
            "intent": Intent(kind="sleep", text="I want to sleep.", duration=wake).model_dump(),
            "origin": agent.location,
            "start": 0,
        }
        changes.extend(
            [
                change("agents", agent.id, agent),
                change("inventories", agent.id, {"id": agent.id, "meals": 12}),
                change("accounts", agent.id, {"id": agent.id, "cents": 10000}),
            ]
        )
        for memory in agent.memories:
            if memory.source != "original_seed":
                continue
            evidence = campaign_knowledge_change(
                owner=agent.id,
                text=memory.text,
                source_id=memory.id,
                source_kind="seed",
                asserted_at=memory.minute,
                observed_at=0,
                speaker=agent.id,
                retained_memory_id=memory.id,
            )
            if evidence:
                changes.append(evidence)
        if config.realism_profile == "connected_v1":
            changes.extend(initial_goal_changes(agent))
    changes.extend(
        [
            change("metadata", "map", town.view()),
            change("metadata", "config", config.model_dump(mode="json")),
            change(
                "metadata",
                "run",
                {
                    "status": "initialized",
                    "completed_minutes": 0,
                    "requested_minutes": 0,
                    "epoch": "2023-02-13T00:00:00+00:00",
                    "benchmark": "valentine",
                    "phase": max(config.phase, 2 if population else 1),
                },
            ),
        ]
    )
    if population:
        agents_by_id = {agent.id: agent for agent in agents}
        changes.extend(change("messages", m.id, m) for m in population.messages)
        changes.extend(change("calendar", e.id, e) for e in population.calendar)
        for message in population.messages:
            sender_memory = next(
                (
                    memory.id
                    for memory in agents_by_id[message.sender].memories
                    if memory.source == message.id
                ),
                None,
            )
            own_evidence = campaign_knowledge_change(
                owner=message.sender,
                text=message.body,
                source_id=message.id,
                source_kind="self_report",
                asserted_at=message.sent_at,
                observed_at=message.sent_at,
                speaker=message.sender,
                listener=message.to,
                retained_memory_id=sender_memory,
            )
            if own_evidence and own_evidence.value["subject"] == message.sender:
                changes.append(own_evidence)
            if message.read_at is not None:
                recipient_memory = next(
                    (
                        memory.id
                        for memory in agents_by_id[message.to].memories
                        if memory.source == message.id
                    ),
                    None,
                )
                exposure = campaign_knowledge_change(
                    owner=message.to,
                    text=message.body,
                    source_id=message.id,
                    source_kind="testimony",
                    asserted_at=message.sent_at,
                    observed_at=message.read_at,
                    speaker=message.sender,
                    listener=message.to,
                    retained_memory_id=recipient_memory,
                )
                if exposure:
                    changes.append(exposure)
        changes.append(
            change(
                "metadata",
                "population",
                {
                    "digest": population.digest or population.fingerprint(),
                    "history_days": population.history_days,
                    "residents": len(population.agents),
                    "historical_messages": len(population.messages),
                    "historical_calendar_entries": len(population.calendar),
                    "consistency_attempts": len(population.consistency),
                    "sources": population.sources,
                },
            )
        )
    if config.phase == 3:
        changes.extend(initial_economy(agents))
        changes.extend(initial_council(agents))
        changes.extend(initial_gathering(agents))
    return world.log.append(0, "initialized", changes=changes)


class Simulation:
    def __init__(
        self,
        directory: Path,
        config: Config,
        *,
        town: MapProvider | None = None,
        cache_path: Path | None = None,
        population: Population | None = None,
    ):
        if config.realism_profile == "connected_v1" and (
            population is None
            or population.history_days < 14
            or any(agent.persona.life_history is None for agent in population.agents)
        ):
            raise ValueError(
                "connected realism requires a validated population with life histories "
                "and at least 14 days of digital history"
            )
        self.config, self.town = (
            config,
            town or SmallvilleMap(extra_locations=population.locations if population else None),
        )
        if population and population.seed != config.seed:
            raise ValueError("population seed differs from run seed; use its recorded seed")
        self.world = WorldState(directory)
        self.clock, self.scheduler, self.bus = SimClock(), Scheduler(), EventBus()
        self.active_agent = None
        self.call_buffer: ContextVar[list | None] = ContextVar("call_buffer", default=None)
        self.wakes: set[tuple[str, int]] = set()
        try:
            bootstrap(self.world, self.town, config, population)
        except Exception:
            self.world.close()
            raise
        backend = (
            MockLLM()
            if config.backend == "mock"
            else LiteLLMBackend(config.timeout_seconds, config.reasoning_effort)
        )
        self.gateway = Gateway(directory, config, backend, cache_path, self._record_call)
        self.mind = Mind(self.world, self.town, self.gateway, config)
        self.gm = GameMaster(self.world, self.town, self.gateway, config)
        self.economy, self.council, self.board = (
            Economy(self.world, config),
            Council(self.world),
            NoticeBoard(self.world),
        )
        for agent in self.world.agents():
            self.scheduler.schedule(agent.busy_until, "complete", agent.id, priority=0)
            self.scheduler.when(
                f"health:{agent.id}",
                lambda identifier=agent.id: self.world.agent(identifier).needs.health < 15,
                "needs_alert",
                agent.id,
            )

    def _record_call(self, record: dict):
        buffer = self.call_buffer.get()
        if buffer is not None:
            buffer.append(record)
        else:
            self.world.log.append(self.clock.minute, "llm_call", self.active_agent, record)

    def wake(self, identifier: str, minute: int):
        key = identifier, minute
        if key not in self.wakes:
            self.wakes.add(key)
            self.scheduler.schedule(minute, "wake", identifier)

    async def _publish(self, event):
        await self.bus.publish(event)
        self.scheduler.check_conditions(self.clock.minute, actor=event.actor)

    async def _wake_batch(self, items, horizon):
        """Read one scene, infer independently, and commit in scheduler order."""
        minute, prepared = items[0].minute, []
        for item in items:
            self.wakes.discard((item.agent, minute))
            if minute >= horizon:
                continue
            actor = self.world.agent(item.agent)
            if actor.busy_until > minute:
                self.wake(actor.id, actor.busy_until)
                continue
            advance_drives(actor, minute)
            changes = self.gm.messaging.read_changes(actor, minute)
            if self.config.phase == 3:
                changes.extend(self.economy.perception_changes(actor, minute))
            changes.append(change("agents", actor.id, actor))
            await self._publish(
                self.world.log.append(
                    minute,
                    "perceived",
                    actor.id,
                    data={
                        "nearby": [
                            peer.id for peer in self.world.at(actor.location) if peer.id != actor.id
                        ]
                        if actor.location is not None
                        else [],
                        "unread_notifications": len(self.gm.messaging.notifications(actor.id)),
                    },
                    changes=changes,
                    observations={actor.id: "I notice my surroundings and check my phone."},
                )
            )
            prepared.append((actor, []))

        async def think(actor, buffer):
            token = self.call_buffer.set(buffer)
            try:
                reflection = None
                if minute % 1440 >= 1260 and actor.last_reflection_day != minute // 1440:
                    reflection = await self.mind.reflect(actor, minute)
                intent = self.mind.continue_routine(actor, minute)
                if intent is not None:
                    return (
                        intent,
                        "routine",
                        {"plan": "reused", "action": "routine", "reflection": reflection},
                    )
                intent = await self.mind.decide(actor, minute)
                diagnostics = self.mind.take_decision_diagnostics() or {
                    "plan": "external",
                    "action": "accepted",
                }
                return intent, "model", diagnostics | {"reflection": reflection}
            finally:
                self.call_buffer.reset(token)

        tasks = [asyncio.create_task(think(actor, buffer)) for actor, buffer in prepared]
        try:
            results = await asyncio.gather(*tasks)
        except BaseException:
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            raise
        finally:
            # Do not expose completion order or another person's tentative plan.
            # In-flight calls are all settled before recording an interruption.
            for actor, buffer in prepared:
                for record in buffer:
                    self.world.log.append(minute, "llm_call", actor.id, record)
        for (actor, _), (intent, source, cognition) in zip(prepared, results):
            self.active_agent = actor.id
            changes = [change("agents", actor.id, actor)]
            if source == "model" and self.config.routine_actions:
                changes.append(self.mind.routine_change(actor, intent, minute))
            await self._publish(
                self.world.log.append(
                    minute,
                    "intention",
                    actor.id,
                    {"intent": intent.model_dump(), "source": source, "cognition": cognition},
                    changes,
                )
            )
            event = await self.gm.resolve(actor.id, intent, minute)
            await self._publish(event)
            actor = self.world.agent(actor.id)
            if event.kind == "action_started":
                self.scheduler.schedule(actor.busy_until, "complete", actor.id, priority=0)
            else:
                self.wake(actor.id, minute + 15)

    async def run(self, days: float = 2) -> dict:
        minutes = days * 1440
        if not math.isfinite(minutes) or minutes <= 0 or int(minutes) != minutes:
            raise ValueError("days must specify a positive integer number of minutes")
        horizon = int(minutes)
        if self.config.phase == 3:
            for day in range(math.ceil(days)):
                for hour, kind in ((360, "economic_morning"), (1260, "economic_rent")):
                    self.scheduler.schedule(day * 1440 + hour, kind, priority=-20)
            self.scheduler.schedule(480, "council_open", priority=-10)
            self.scheduler.schedule(3600, "council_close", priority=-10)
        status, problem = "completed", None
        try:
            while self.scheduler.queue and self.scheduler.queue[0].minute <= horizon:
                item = self.scheduler.pop()
                self.clock.advance(item.minute)
                self.active_agent = item.agent
                if item.kind == "economic_morning":
                    await self._publish(self.economy.allowances(item.minute))
                    stock_event = self.economy.restock(item.minute)
                    await self._publish(stock_event)
                    body = (
                        "Today's wholesale delivery is delayed. Existing shop stock is finite. "
                        if stock_event.data["delivery_delayed"]
                        else f"Shops received {stock_event.data['delivered_meals']} replenishment meals. "
                    )
                    body += "Reported morning meal stocks: " + ", ".join(
                        f"{self.world.location(key).name}: {value}"
                        for key, value in stock_event.data["stock"].items()
                    )
                    await self._publish(
                        self.board.publish(
                            item.minute,
                            "Local food supply bulletin",
                            body,
                            sources=[stock_event.seq],
                            shop_reports=stock_event.data["stock"],
                        )
                    )
                elif item.kind == "economic_rent":
                    await self._publish(self.economy.rent(item.minute))
                elif item.kind == "council_open":
                    await self._publish(self.council.open(item.minute))
                elif item.kind == "council_close":
                    await self._publish(self.council.close(item.minute))
                elif item.kind == "complete":
                    event = self.gm.complete(item.agent, item.minute)
                    await self._publish(event)
                    actor = self.world.agent(item.agent)
                    if actor.pending:
                        self.scheduler.schedule(actor.busy_until, "complete", actor.id, priority=0)
                    elif item.minute < horizon:
                        self.wake(actor.id, item.minute)
                    if recipient := event.data.get("recipient"):
                        peer = self.world.agent(recipient)
                        self.wake(recipient, max(item.minute, peer.busy_until))
                elif item.kind == "needs_alert":
                    actor = self.world.agent(item.agent)
                    actor.surprise = True
                    await self._publish(
                        self.world.log.append(
                            item.minute,
                            "needs_alert",
                            actor.id,
                            changes=[change("agents", actor.id, actor)],
                            observations={
                                actor.id: "I feel unwell and need to reconsider my plans."
                            },
                        )
                    )
                    self.wake(actor.id, max(item.minute, actor.busy_until))
                elif item.kind == "wake":
                    items = [item]
                    while len(items) < self.config.decision_concurrency and self.scheduler.queue:
                        next_item = self.scheduler.queue[0]
                        if next_item.kind != "wake" or next_item.minute != item.minute:
                            break
                        items.append(self.scheduler.pop())
                    await self._wake_batch(items, horizon)
                await asyncio.sleep(0)  # Cooperative scheduling, never wall-time simulation.
        except asyncio.CancelledError:
            status, problem = "interrupted", "operator cancelled the simulation"
        except BudgetExceeded:
            status, problem = (
                "budget_stopped",
                "next model call exceeded remaining reservation budget",
            )
        except ModelFailure as error:
            suffix = f" (HTTP {error.status_code})" if error.status_code is not None else ""
            status, problem = (
                "model_stopped",
                "model request failed or exact cache entry was missing" + suffix,
            )
        if status == "completed":
            self.clock.advance(horizon)
        changes = []
        for actor in self.world.agents():
            advance_drives(actor, self.clock.minute)
            changes.append(change("agents", actor.id, actor))
        run = self.world.get("metadata", "run") | {
            "status": status,
            "completed_minutes": self.clock.minute,
            "requested_minutes": horizon,
            "problem": problem,
        }
        changes.append(change("metadata", "run", run))
        await self._publish(
            self.world.log.append(
                self.clock.minute,
                "run_finished",
                data=run,
                changes=changes,
            )
        )
        return run | {"agents": len(self.world.agents()), "cost": self.gateway.summary()}

    def close(self):
        self.gateway.close()
        self.world.close()
