from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class Location(Model):
    id: str
    name: str
    address: str
    x: int
    y: int
    capacity: int = Field(default=30, ge=1)
    opens: int = Field(default=0, ge=0, le=1439)
    closes: int = Field(default=1440, ge=1, le=1440)
    private: bool = False

    def is_open(self, minute: int) -> bool:
        time = minute % 1440
        if self.opens < self.closes:
            return self.opens <= time < self.closes
        return time >= self.opens or time < self.closes

    def open_throughout(self, start: int, end: int) -> bool:
        return all(self.is_open(m) for m in range(start, end))


class Needs(Model):
    fullness: float = Field(default=80, ge=0, le=100)
    social: float = Field(default=70, ge=0, le=100)
    health: float = Field(default=95, ge=0, le=100)
    fun: float = Field(default=65, ge=0, le=100)
    energy: float = Field(default=70, ge=0, le=100)


class Emotion(Model):
    valence: float = Field(default=0, ge=-1, le=1)
    arousal: float = Field(default=0.2, ge=0, le=1)
    label: str = "neutral"


class LifeEvent(Model):
    age: int = Field(ge=0, le=120)
    description: str = Field(min_length=10, max_length=600)


class LifeHistory(Model):
    narrative: str = Field(min_length=120, max_length=6000)
    events: list[LifeEvent] = Field(min_length=6, max_length=12)
    interests: list[str] = Field(min_length=2, max_length=8)
    values: list[str] = Field(min_length=2, max_length=8)
    goals: list[str] = Field(min_length=2, max_length=8)


class Persona(Model):
    name: str
    age: int = Field(ge=0, le=120)
    description: str
    traits: str
    lifestyle: str
    speech_style: str
    home: str
    workplace: str
    tier: Literal["deep", "standard"] = "standard"
    temperature: float = Field(default=0.7, ge=0, le=2)
    sociability: float = Field(default=0.5, ge=0, le=1)
    opinion: float = Field(default=0, ge=-1, le=1)
    known_locations: list[str] = Field(default_factory=list)
    facts: dict[str, str | int | float] = Field(default_factory=dict)
    life_history: LifeHistory | None = None
    provenance: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def coherent_history(self):
        if self.life_history and any(e.age > self.age for e in self.life_history.events):
            raise ValueError("life history contains an event after the person's current age")
        if self.life_history and [e.age for e in self.life_history.events] != sorted(
            e.age for e in self.life_history.events
        ):
            raise ValueError("life history must be in chronological order")
        for key, value in (
            ("name", self.name),
            ("age", self.age),
            ("home", self.home),
            ("workplace", self.workplace),
        ):
            if key in self.facts and self.facts[key] != value:
                raise ValueError(f"persona fact disagrees with {key}")
        return self


class Memory(Model):
    id: str
    minute: int
    text: str
    importance: float = Field(default=0.5, ge=0, le=1)
    kind: Literal["episode", "reflection", "seed"] = "episode"
    source: str
    last_access: int = 0
    repetitions: int = Field(default=1, ge=1)


class ArchivedMemory(Model):
    """A private evicted episode; retrieval remains owner-scoped and bounded."""

    id: str
    owner: str
    memory: Memory
    archived_at: int
    reason: Literal["capacity"] = "capacity"


class Goal(Model):
    id: str
    owner: str
    description: str = Field(min_length=3, max_length=1000)
    status: Literal["active", "blocked", "completed", "abandoned"] = "active"
    priority: float = Field(default=0.5, ge=0, le=1)
    source: Literal["original_seed", "generated_life_history", "resident", "commitment"]
    created_at: int = 0
    updated_at: int = 0
    deadline: int | None = None
    progress: str = Field(default="not_started", max_length=500)
    prerequisites: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def valid_times(self):
        if self.deadline is not None and self.deadline < self.created_at:
            raise ValueError("goal deadline precedes its creation")
        return self


class GoalTransition(Model):
    id: str
    goal_id: str
    owner: str
    minute: int
    action: Literal["revise", "block", "activate", "complete", "abandon"]
    old_status: Literal["active", "blocked", "completed", "abandoned"]
    new_status: Literal["active", "blocked", "completed", "abandoned"]
    reason: str = Field(min_length=3, max_length=500)
    evidence: list[str] = Field(default_factory=list)


class KnowledgeEvidence(Model):
    """Owner-scoped evidence about a claim, never an omniscient truth record."""

    id: str
    owner: str
    subject: str
    predicate: Literal["mayoral_candidacy"]
    claim_status: Literal["considering", "declared", "denied", "unknown"]
    epistemic_status: Literal["exposed", "accepted", "rejected"]
    source_kind: Literal["seed", "self_report", "testimony", "world_event"]
    source_id: str
    asserted_at: int
    observed_at: int
    text: str = Field(min_length=1, max_length=4000)
    confidence: float = Field(default=0.5, ge=0, le=1)
    retained_memory_id: str | None = None


class PlanBlock(Model):
    start: int = Field(ge=0, lt=1440)
    end: int = Field(gt=0, le=1440)
    activity: Literal["sleep", "eat", "work", "leisure"]
    location: str

    @model_validator(mode="after")
    def ordered(self):
        if self.end <= self.start:
            raise ValueError("plan block must have positive duration")
        return self


class DailyPlan(Model):
    day: int = Field(ge=0)
    blocks: list[PlanBlock] = Field(min_length=1, max_length=32)

    @model_validator(mode="after")
    def nonoverlapping(self):
        if self.blocks[0].start != 0 or self.blocks[-1].end != 1440:
            raise ValueError("daily plan must cover the day")
        for previous, current in zip(self.blocks, self.blocks[1:]):
            if previous.end != current.start:
                raise ValueError("daily plan must be contiguous and ordered")
        return self


class Agent(Model):
    id: str
    persona: Persona
    location: str | None
    destination: str | None = None
    activity: str = "sleep"
    busy_until: int = Field(default=0, ge=0)
    updated_at: int = Field(default=0, ge=0)
    needs: Needs = Field(default_factory=Needs)
    emotion: Emotion = Field(default_factory=Emotion)
    contacts: list[str] = Field(default_factory=list)
    relationships: dict[str, float] = Field(default_factory=dict)
    memories: list[Memory] = Field(default_factory=list)
    plan: DailyPlan | None = None
    last_reflection_day: int = -1
    surprise: bool = False
    last_social_at: int = -60
    pending: dict[str, Any] | None = None
    activity_minutes: dict[str, int] = Field(default_factory=dict)


ActionKind = Literal[
    "move",
    "sleep",
    "eat",
    "work",
    "leisure",
    "wait",
    "message",
    "calendar",
    "attend",
    "attempt",
    "buy",
    "transfer",
    "read_news",
    "post_notice",
    "vote",
    "goal",
]


class Intent(Model):
    kind: ActionKind
    text: str = Field(min_length=1, max_length=2000)
    target: str | None = None
    duration: int = Field(default=60, ge=1, le=480)
    arguments: dict[str, Any] = Field(default_factory=dict)


class Message(Model):
    id: str
    sender: str
    to: str
    body: str = Field(min_length=1, max_length=2000)
    sent_at: int
    read_at: int | None = None
    verbosity: Literal["quiet", "normal", "urgent"] = "normal"

    @model_validator(mode="after")
    def read_follows_send(self):
        if self.read_at is not None and self.read_at < self.sent_at:
            raise ValueError("message cannot be read before it was sent")
        return self


class CalendarEntry(Model):
    id: str
    owner: str
    title: str = Field(min_length=1, max_length=200)
    start: int
    end: int
    location: str
    attendees: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def positive_duration(self):
        if self.end <= self.start:
            raise ValueError("calendar end must follow start")
        return self


TABLES = (
    "agents",
    "locations",
    "objects",
    "inventories",
    "accounts",
    "jobs",
    "messages",
    "calendar",
    "transfers",
    "leases",
    "shops",
    "shop_observations",
    "news",
    "news_reads",
    "proposals",
    "ballots",
    "gatherings",
    "invitations",
    "event_rsvps",
    "goals",
    "goal_history",
    "memory_archive",
    "knowledge",
    "metadata",
)


class Change(Model):
    table: Literal[
        "agents",
        "locations",
        "objects",
        "inventories",
        "accounts",
        "jobs",
        "messages",
        "calendar",
        "transfers",
        "leases",
        "shops",
        "shop_observations",
        "news",
        "news_reads",
        "proposals",
        "ballots",
        "gatherings",
        "invitations",
        "event_rsvps",
        "goals",
        "goal_history",
        "memory_archive",
        "knowledge",
        "metadata",
    ]
    id: str
    value: dict[str, Any]


def change(table: str, identifier: str, value: BaseModel | dict) -> Change:
    return Change(
        table=table,
        id=identifier,
        value=value.model_dump(mode="json") if isinstance(value, BaseModel) else value,
    )
