from typing import Literal

from pydantic import Field

from smallville.agents.drives import conversation_effect
from smallville.agents.memory import remember
from smallville.world.models import Agent, CalendarEntry, Change, Message, Model, change
from smallville.world.store import WorldState


class SendMessage(Model):
    to: str
    body: str = Field(min_length=1, max_length=2000)
    verbosity: Literal["quiet", "normal", "urgent"] = "normal"


class CreateEvent(Model):
    title: str = Field(min_length=1, max_length=200)
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    location: str


class Messaging:
    def __init__(self, world: WorldState):
        self.world = world

    def validate(self, actor: Agent, request: SendMessage) -> None:
        if request.to == actor.id:
            raise ValueError("cannot message myself")
        recipient = self.world.agent(request.to)
        if request.to not in actor.contacts and (
            actor.location is None or actor.location != recipient.location
        ):
            raise ValueError("I do not have this person's contact")

    def delivery_changes(
        self, actor: Agent, request: SendMessage, minute: int
    ) -> tuple[Message, list[Change]]:
        self.validate(actor, request)
        identifier = f"msg:{actor.id}:{minute}"
        message = Message(
            id=identifier,
            sender=actor.id,
            to=request.to,
            body=request.body,
            sent_at=minute,
            verbosity=request.verbosity,
        )
        if request.to not in actor.contacts:
            actor.contacts.append(request.to)
        conversation_effect(actor, request.to, request.body)
        remember(actor, minute, f"I sent {request.to}: {request.body}", identifier, 0.65)
        actor.last_social_at = minute
        return message, [change("messages", identifier, message)]

    def inbox(self, owner: str) -> list[Message]:
        self.world.agent(owner)
        return [m for m in self.world.messages(owner) if m.to == owner]

    def read_changes(self, actor: Agent, minute: int) -> list[Change]:
        changes = []
        for message in self.inbox(actor.id):
            if message.read_at is not None or message.sent_at > minute:
                continue
            message.read_at = minute
            remember(actor, minute, f"{message.sender} told me: {message.body}", message.id, 0.85)
            if message.sender not in actor.contacts:
                actor.contacts.append(message.sender)
            conversation_effect(actor, message.sender, message.body)
            actor.surprise = True
            changes.append(change("messages", message.id, message))
        return changes

    def notifications(
        self, owner: str, verbosity: Literal["quiet", "normal", "verbose"] = "normal"
    ) -> list[dict]:
        messages = [m for m in self.inbox(owner) if m.read_at is None]
        if verbosity == "quiet":
            messages = [m for m in messages if m.verbosity == "urgent"]
        return [
            {
                "id": m.id,
                "from": m.sender,
                "sent_at": m.sent_at,
                "body": m.body if verbosity == "verbose" else m.body[:120],
            }
            for m in messages[-8:]
        ]


class Calendar:
    def __init__(self, world: WorldState):
        self.world = world

    def validate(self, actor: Agent, request: CreateEvent, minute: int) -> None:
        if request.end <= request.start or request.start < minute:
            raise ValueError("calendar times must be future and ordered")
        if request.location not in actor.persona.known_locations:
            raise ValueError("unknown calendar location")
        if not self.world.location(request.location).open_throughout(request.start, request.end):
            raise ValueError("location closed during calendar entry")
        for event in self.world.calendar(actor.id):
            if request.start < event.end and event.start < request.end:
                raise ValueError("calendar conflict")

    def create_changes(self, actor: Agent, request: CreateEvent, minute: int) -> list[Change]:
        self.validate(actor, request, minute)
        identifier = f"cal:{actor.id}:{minute}"
        event = CalendarEntry(id=identifier, owner=actor.id, **request.model_dump())
        remember(actor, minute, f"I scheduled {event.title} at {event.location}.", identifier, 0.75)
        return [change("calendar", identifier, event)]

    def list_events(self, owner: str) -> list[CalendarEntry]:
        self.world.agent(owner)
        return self.world.calendar(owner)
