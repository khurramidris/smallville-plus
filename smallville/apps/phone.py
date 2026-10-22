from typing import Literal

from pydantic import Field

from smallville.agents.drives import conversation_effect
from smallville.agents.knowledge import campaign_knowledge_change
from smallville.agents.memory import archive_changes, remember
from smallville.agents.relationships import contact_change
from smallville.apps.gatherings import Gatherings
from smallville.world.models import (
    Agent,
    CalendarEntry,
    Change,
    Message,
    Model,
    PhoneAttention,
    change,
)
from smallville.world.store import WorldState


class SendMessage(Model):
    to: str
    body: str = Field(min_length=1, max_length=2000)
    verbosity: Literal["quiet", "normal", "urgent"] = "normal"
    event_id: str | None = None


class CreateEvent(Model):
    title: str = Field(min_length=1, max_length=200)
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    location: str
    event_id: str | None = None


class Messaging:
    def __init__(self, world: WorldState):
        self.world = world

    def connected(self) -> bool:
        try:
            return self.world.get("metadata", "config").get("realism_profile") == "connected_v1"
        except KeyError:
            return False

    def validate(self, actor: Agent, request: SendMessage) -> None:
        if request.to == actor.id:
            raise ValueError("cannot message myself")
        recipient = self.world.agent(request.to)
        if request.to not in actor.contacts and (
            actor.location is None or actor.location != recipient.location
        ):
            raise ValueError("I do not have this person's contact")
        if request.event_id:
            Gatherings(self.world).attachment(actor, request.body, request.event_id)

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
        if self.connected():
            actor.needs.social = min(100, actor.needs.social + 2)
        else:
            conversation_effect(actor, request.to, request.body)
        evicted = []
        memory = remember(
            actor,
            minute,
            f"I sent {request.to}: {request.body}",
            identifier,
            0.65,
            evicted=evicted,
        )
        actor.last_social_at = minute
        evidence = campaign_knowledge_change(
            owner=actor.id,
            text=request.body,
            source_id=identifier,
            source_kind="self_report",
            asserted_at=minute,
            observed_at=minute,
            speaker=actor.id,
            listener=request.to,
            retained_memory_id=memory.id,
        )
        relationship_changes = (
            [contact_change(self.world, actor, request.to, minute, identifier)]
            if self.connected()
            else []
        )
        return message, [
            change("messages", identifier, message),
            *([evidence] if evidence is not None and evidence.value["subject"] == actor.id else []),
            *Gatherings(self.world).invitation_changes(
                actor, request.body, request.event_id, identifier, request.to
            ),
            *relationship_changes,
            *archive_changes(actor.id, evicted, minute),
        ]

    def inbox(self, owner: str) -> list[Message]:
        self.world.agent(owner)
        return [m for m in self.world.messages(owner) if m.to == owner]

    def read_batch(
        self, actor: Agent, minute: int, limit: int | None = None
    ) -> tuple[list[Change], list[str]]:
        changes, evicted = [], []
        unread = [
            message
            for message in self.inbox(actor.id)
            if message.read_at is None and message.sent_at <= minute
        ]
        unread.sort(
            key=lambda message: (
                0 if message.verbosity == "urgent" else 1,
                message.sent_at,
                message.id,
            )
        )
        selected = unread[:limit] if limit is not None else unread
        for message in selected:
            message.read_at = minute
            memory = remember(
                actor,
                minute,
                f"{message.sender} told me: {message.body}",
                message.id,
                0.85,
                evicted=evicted,
            )
            if message.sender not in actor.contacts:
                actor.contacts.append(message.sender)
            if self.connected():
                actor.needs.social = min(100, actor.needs.social + 2)
                changes.append(
                    contact_change(self.world, actor, message.sender, minute, message.id)
                )
            else:
                conversation_effect(actor, message.sender, message.body)
            actor.surprise = True
            changes.append(change("messages", message.id, message))
            evidence = campaign_knowledge_change(
                owner=actor.id,
                text=message.body,
                source_id=message.id,
                source_kind="testimony",
                asserted_at=message.sent_at,
                observed_at=minute,
                speaker=message.sender,
                listener=actor.id,
                retained_memory_id=memory.id,
            )
            if evidence:
                changes.append(evidence)
        changes.extend(archive_changes(actor.id, evicted, minute))
        return changes, [message.id for message in selected]

    def read_changes(self, actor: Agent, minute: int, limit: int | None = None) -> list[Change]:
        return self.read_batch(actor, minute, limit)[0]

    def attention(self, owner: str) -> PhoneAttention:
        try:
            return PhoneAttention.model_validate(self.world.get("phone_attention", owner))
        except KeyError:
            return PhoneAttention(id=owner, owner=owner)

    def check_changes(
        self, actor: Agent, minute: int, limit: int = 2
    ) -> tuple[list[Change], list[str], int]:
        changes, read = self.read_batch(actor, minute, limit)
        attention = self.attention(actor.id)
        attention.last_checked = minute
        attention.checks += 1
        attention.messages_read += len(read)
        remaining = len(
            [
                message
                for message in self.inbox(actor.id)
                if message.read_at is None and message.sent_at <= minute and message.id not in read
            ]
        )
        changes.append(change("phone_attention", attention.id, attention))
        return changes, read, remaining

    def notifications(
        self,
        owner: str,
        verbosity: Literal["quiet", "normal", "verbose", "summary"] = "normal",
    ) -> list[dict]:
        messages = [m for m in self.inbox(owner) if m.read_at is None]
        if verbosity == "quiet":
            messages = [m for m in messages if m.verbosity == "urgent"]
        return [
            {
                "id": m.id,
                "from": m.sender,
                "sent_at": m.sent_at,
                "verbosity": m.verbosity,
                **(
                    {}
                    if verbosity == "summary"
                    else {"body": m.body if verbosity == "verbose" else m.body[:120]}
                ),
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
        Gatherings(self.world).calendar_event(actor, request)
        for event in self.world.calendar(actor.id):
            if request.start < event.end and event.start < request.end:
                raise ValueError("calendar conflict")

    def create_changes(self, actor: Agent, request: CreateEvent, minute: int) -> list[Change]:
        self.validate(actor, request, minute)
        identifier = f"cal:{actor.id}:{minute}"
        event = CalendarEntry(
            id=identifier, owner=actor.id, **request.model_dump(exclude={"event_id"})
        )
        evicted = []
        remember(
            actor,
            minute,
            f"I scheduled {event.title} at {event.location}.",
            identifier,
            0.75,
            evicted=evicted,
        )
        shared = Gatherings(self.world).calendar_event(actor, request)
        links = (
            [
                change(
                    "event_rsvps",
                    identifier,
                    {"id": identifier, "owner": actor.id, "event_id": shared["id"]},
                )
            ]
            if shared
            else []
        )
        return [
            change("calendar", identifier, event),
            *links,
            *archive_changes(actor.id, evicted, minute),
        ]

    def list_events(self, owner: str) -> list[CalendarEntry]:
        self.world.agent(owner)
        return self.world.calendar(owner)
