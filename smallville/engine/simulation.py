from __future__ import annotations

import asyncio
import math
from pathlib import Path

from smallville.agents.drives import advance_drives
from smallville.agents.mind import Mind
from smallville.config import Config
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
                    "phase": 2 if population else 1,
                },
            ),
        ]
    )
    if population:
        changes.extend(change("messages", m.id, m) for m in population.messages)
        changes.extend(change("calendar", e.id, e) for e in population.calendar)
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
        self.config, self.town = (
            config,
            town or SmallvilleMap(extra_locations=population.locations if population else None),
        )
        if population and population.seed != config.seed:
            raise ValueError("population seed differs from run seed; use its recorded seed")
        self.world = WorldState(directory)
        self.clock, self.scheduler, self.bus = SimClock(), Scheduler(), EventBus()
        self.active_agent = None
        self.wakes: set[tuple[str, int]] = set()
        try:
            bootstrap(self.world, self.town, config, population)
        except Exception:
            self.world.close()
            raise
        backend = MockLLM() if config.backend == "mock" else LiteLLMBackend(config.timeout_seconds)
        self.gateway = Gateway(directory, config, backend, cache_path, self._record_call)
        self.mind = Mind(self.world, self.town, self.gateway, config)
        self.gm = GameMaster(self.world, self.town, self.gateway, config)
        for agent in self.world.agents():
            self.scheduler.schedule(agent.busy_until, "complete", agent.id, priority=0)
            self.scheduler.when(
                f"health:{agent.id}",
                lambda identifier=agent.id: self.world.agent(identifier).needs.health < 15,
                "needs_alert",
                agent.id,
            )

    def _record_call(self, record: dict):
        self.world.log.append(self.clock.minute, "llm_call", self.active_agent, record)

    def wake(self, identifier: str, minute: int):
        key = identifier, minute
        if key not in self.wakes:
            self.wakes.add(key)
            self.scheduler.schedule(minute, "wake", identifier)

    async def _publish(self, event):
        await self.bus.publish(event)
        self.scheduler.check_conditions(self.clock.minute, actor=event.actor)

    async def run(self, days: float = 2) -> dict:
        minutes = days * 1440
        if not math.isfinite(minutes) or minutes <= 0 or int(minutes) != minutes:
            raise ValueError("days must specify a positive integer number of minutes")
        horizon = int(minutes)
        status, problem = "completed", None
        try:
            while self.scheduler.queue and self.scheduler.queue[0].minute <= horizon:
                item = self.scheduler.pop()
                self.clock.advance(item.minute)
                self.active_agent = item.agent
                if item.kind == "complete":
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
                    self.wakes.discard((item.agent, item.minute))
                    if item.minute >= horizon:
                        continue
                    actor = self.world.agent(item.agent)
                    if actor.busy_until > item.minute:
                        self.wake(actor.id, actor.busy_until)
                        continue
                    advance_drives(actor, item.minute)
                    changes = self.gm.messaging.read_changes(actor, item.minute)
                    changes.append(change("agents", actor.id, actor))
                    await self._publish(
                        self.world.log.append(
                            item.minute,
                            "perceived",
                            actor.id,
                            changes=changes,
                            observations={actor.id: "I notice my surroundings and check my phone."},
                        )
                    )
                    if (
                        item.minute % 1440 >= 1260
                        and actor.last_reflection_day != item.minute // 1440
                    ):
                        await self.mind.reflect(actor, item.minute)
                    intent = await self.mind.decide(actor, item.minute)
                    await self._publish(
                        self.world.log.append(
                            item.minute,
                            "intention",
                            actor.id,
                            {"intent": intent.model_dump()},
                            [change("agents", actor.id, actor)],
                        )
                    )
                    event = await self.gm.resolve(actor.id, intent, item.minute)
                    await self._publish(event)
                    actor = self.world.agent(actor.id)
                    if event.kind == "action_started":
                        self.scheduler.schedule(actor.busy_until, "complete", actor.id, priority=0)
                    else:
                        self.wake(actor.id, item.minute + 15)
                await asyncio.sleep(0)  # Cooperative scheduling, never wall-time simulation.
        except BudgetExceeded:
            status, problem = (
                "budget_stopped",
                "next model call exceeded remaining reservation budget",
            )
        except ModelFailure:
            status, problem = (
                "model_stopped",
                "model request failed or exact cache entry was missing",
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
