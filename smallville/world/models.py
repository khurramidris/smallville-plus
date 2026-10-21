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


class Memory(Model):
    id: str
    minute: int = Field(ge=0)
    text: str
    importance: float = Field(default=0.5, ge=0, le=1)
    kind: Literal["episode", "reflection", "seed"] = "episode"
    source: str
    last_access: int = Field(default=0, ge=0)


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
    "move", "sleep", "eat", "work", "leisure", "wait", "message", "calendar", "attend", "attempt"
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
    sent_at: int = Field(ge=0)
    read_at: int | None = None
    verbosity: Literal["quiet", "normal", "urgent"] = "normal"


class CalendarEntry(Model):
    id: str
    owner: str
    title: str = Field(min_length=1, max_length=200)
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    location: str

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
