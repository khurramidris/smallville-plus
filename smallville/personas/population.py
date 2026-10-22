from __future__ import annotations

import hashlib
from collections import Counter
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from smallville.engine.events import canonical
from smallville.personas.consistency import ConsistencyAttempt
from smallville.personas.generation import source_population
from smallville.personas.seeds import load_agents
from smallville.world.maps import MapProvider
from smallville.world.models import Agent, CalendarEntry, Location, Message, Model


class Population(Model):
    version: Literal[2, 3] = 3
    seed: int
    history_days: int = Field(ge=14, le=60)
    agents: list[Agent] = Field(min_length=25, max_length=100)
    locations: list[Location] = Field(default_factory=list)
    messages: list[Message]
    calendar: list[CalendarEntry]
    consistency: list[ConsistencyAttempt]
    sources: dict[str, str]
    digest: str = ""

    def fingerprint(self) -> str:
        return hashlib.sha256(
            canonical(self.model_dump(mode="json", exclude={"digest"})).encode()
        ).hexdigest()

    @model_validator(mode="after")
    def validate_structure(self):
        identifiers = {a.id for a in self.agents}
        if len(identifiers) != len(self.agents):
            raise ValueError("duplicate resident IDs")
        if len({loc.id for loc in self.locations}) != len(self.locations):
            raise ValueError("duplicate residential unit IDs")
        by_id = {a.id: a for a in self.agents}
        latest = {a.resident: a for a in self.consistency}
        if set(latest) != identifiers or not all(a.passed for a in latest.values()):
            raise ValueError("every resident must pass t=0 consistency before launch")
        for a in self.agents:
            if (
                a.persona.life_history is None
                or a.updated_at != 0
                or a.pending
                or a.busy_until != 0
            ):
                raise ValueError(
                    "population must contain complete profiles at t=0, before scheduling"
                )
            if a.location != a.persona.home or any(
                c not in identifiers or c == a.id for c in a.contacts
            ):
                raise ValueError("invalid initial location or contact")
        if len({m.id for m in self.messages}) != len(self.messages):
            raise ValueError("duplicate historical message IDs")
        for m in self.messages:
            if m.sender not in identifiers or m.to not in identifiers or m.sender == m.to:
                raise ValueError("invalid historical message participant")
            if m.to not in by_id[m.sender].contacts or m.sender not in by_id[m.to].contacts:
                raise ValueError("historical conversation requires reciprocal contacts")
            if m.sent_at >= 0 or (m.read_at is not None and m.read_at > 0):
                raise ValueError("digital history must precede the simulation epoch")
        for actor in self.agents:
            dates = {m.sent_at // 1440 for m in self.messages if actor.id in (m.sender, m.to)}
            if len(dates) < self.history_days:
                raise ValueError("resident has insufficient daily digital history")
        if self.version >= 3:
            messages_by_id = {message.id: message for message in self.messages}
            for actor in self.agents:
                commitments = [
                    memory
                    for memory in actor.memories
                    if memory.source.startswith("historical_commitment:")
                ]
                if not commitments:
                    raise ValueError("resident has no unfinished historical commitment")
                for memory in commitments:
                    _, deadline, message_id = memory.source.split(":", 2)
                    if not deadline.isdigit() or int(deadline) <= 0:
                        raise ValueError("historical commitment must have a future deadline")
                    if (
                        message_id not in messages_by_id
                        or messages_by_id[message_id].sender != actor.id
                    ):
                        raise ValueError("historical commitment lacks the resident's acceptance")
        if len({e.id for e in self.calendar}) != len(self.calendar):
            raise ValueError("duplicate calendar IDs")
        for e in self.calendar:
            if e.owner not in identifiers or e.end > 0 or e.start >= 0:
                raise ValueError("invalid past calendar entry")
            if set(e.attendees) - identifiers or e.owner not in e.attendees:
                raise ValueError("invalid calendar attendees")
        if self.digest and self.digest != self.fingerprint():
            raise ValueError("population artifact digest does not match its content")
        return self

    def validate_map(self, town: MapProvider):
        by_id = {a.id: a for a in self.agents}
        expected, _ = source_population(town, len(self.agents), self.seed)
        if {a.id for a in expected} != by_id.keys():
            raise ValueError("population IDs do not match the recorded licensed seed subset")
        for baseline in expected:
            if by_id[baseline.id].persona.facts != baseline.persona.facts:
                raise ValueError("locked source facts changed after generation")
        for original in load_agents(town, self.seed):
            actual = by_id.get(original.id)
            if actual is None or any(
                getattr(actual.persona, k) != getattr(original.persona, k)
                for k in ("name", "age", "home", "workplace")
            ):
                raise ValueError("original 25 seed identity facts must be preserved")
            original_memories = {m.text for m in original.memories if m.source == "original_seed"}
            if not original_memories <= {
                m.text for m in actual.memories if m.source == "original_seed"
            }:
                raise ValueError("original seed memories and goals must be preserved")
        occupancy = Counter(a.persona.home for a in self.agents)
        for agent in self.agents:
            if set(agent.persona.known_locations) - town.locations.keys():
                raise ValueError("persona refers to unknown map locations")
            if occupancy[agent.persona.home] > town.locations[agent.persona.home].capacity:
                raise ValueError("initial home capacity exceeded")
        for entry in self.calendar:
            if entry.location not in town.locations or not town.locations[
                entry.location
            ].open_throughout(entry.start, entry.end):
                raise ValueError("historical appointment is at an unknown or closed venue")
        for agent in self.agents:
            entries = sorted(
                (e for e in self.calendar if e.owner == agent.id), key=lambda e: e.start
            )
            for previous, current in zip(entries, entries[1:]):
                travel = town.travel_minutes(previous.location, current.location)
                if previous.end + travel > current.start:
                    raise ValueError("historical calendar entries conflict with time or travel")
        # Personal copies of a shared meeting count each actual attendee once.
        for minute in {e.start for e in self.calendar}:
            for location in {e.location for e in self.calendar if e.start == minute}:
                owners = {
                    e.owner
                    for e in self.calendar
                    if e.location == location and e.start <= minute < e.end
                }
                if len(owners) > town.locations[location].capacity:
                    raise ValueError("historical meeting exceeds venue capacity")

    def save(self, path: Path):
        self.digest = self.fingerprint()
        # Validate the complete artifact again before atomic publication.
        self.model_validate(self.model_dump())
        temporary = path.with_suffix(path.suffix + ".tmp")
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary.write_text(self.model_dump_json(indent=2) + "\n")
        temporary.replace(path)

    @classmethod
    def load(cls, path: Path) -> Population:
        result = cls.model_validate_json(path.read_text())
        if not result.digest:
            raise ValueError("population artifact must carry a content digest")
        return result
