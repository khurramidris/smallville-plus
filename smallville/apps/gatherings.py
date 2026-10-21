"""Shared events are host-owned facts; private calendar entries are intentions."""

import re

from smallville.agents.knowledge import clock_time_evidence
from smallville.engine.clock import SimClock
from smallville.world.models import Agent, CalendarEntry, change
from smallville.world.store import WorldState


def words(text: str):
    return set(re.findall(r"[a-z]{4,}", text.lower())) - {
        "party",
        "event",
        "meeting",
        "with",
        "from",
        "this",
        "that",
        "have",
        "will",
    }


def initial_gathering(agents: list[Agent]):
    if not any(a.id == "isabella_rodriguez" for a in agents):
        return []
    event = {
        "id": "valentine_2023",
        "host": "isabella_rodriguez",
        "title": "Valentine's party",
        "start": 2460,
        "end": 2580,
        "location": "hobbs_cafe",
        "active": True,
    }
    entry = CalendarEntry(
        id="cal:valentine:host",
        owner=event["host"],
        title=event["title"],
        start=event["start"],
        end=event["end"],
        location=event["location"],
    )
    return [
        change("gatherings", event["id"], event),
        change("calendar", entry.id, entry),
        change(
            "event_rsvps", entry.id, {"id": entry.id, "owner": entry.owner, "event_id": event["id"]}
        ),
    ]


class Gatherings:
    def __init__(self, world: WorldState):
        self.world = world

    def visible(self, actor: Agent):
        known = set()
        for invite in self.world.all("invitations"):
            if invite["to"] == actor.id:
                message = self.world.get("messages", invite["message_id"])
                if message["read_at"] is not None:
                    known.add(invite["event_id"])
        return [
            e for e in self.world.all("gatherings") if e["host"] == actor.id or e["id"] in known
        ]

    def attachment(self, actor: Agent, body: str, identifier: str | None):
        events = self.visible(actor)
        if identifier:
            matches = [e for e in events if e["id"] == identifier]
            if not matches:
                raise ValueError("I have not received that event")
            return matches[0]
        # Support complete natural-language invitations as well as structured
        # phone attachments. Only match events the sender already knows.
        for event in events:
            date = SimClock(event["start"]).now
            low = body.lower()
            has_time = clock_time_evidence(body, date.hour, date.minute)
            has_date = (
                date.date().isoformat() in low or f"{date.strftime('%B').lower()} {date.day}" in low
            )
            venue = self.world.location(event["location"]).name.lower().split()[0]
            if has_date and has_time and venue in low and words(event["title"]) & words(body):
                return event
        return None

    def invitation_changes(
        self, actor: Agent, body: str, identifier: str | None, message_id: str, recipient: str
    ):
        event = self.attachment(actor, body, identifier)
        if event is None:
            return []
        key = f"invite:{message_id}"
        return [
            change(
                "invitations",
                key,
                {
                    "id": key,
                    "event_id": event["id"],
                    "message_id": message_id,
                    "from": actor.id,
                    "to": recipient,
                },
            )
        ]

    def calendar_event(self, actor: Agent, request):
        events = self.visible(actor)
        if request.event_id:
            events = [e for e in events if e["id"] == request.event_id]
            if not events:
                raise ValueError("unknown shared event")
        else:
            events = [
                e
                for e in events
                if e["location"] == request.location and words(e["title"]) & words(request.title)
            ]
        if len(events) > 1:
            raise ValueError("choose the specific shared event ID")
        if not events:
            return None
        event = events[0]
        if (
            not event["active"]
            or request.location != event["location"]
            or not event["start"] <= request.start < request.end <= event["end"]
        ):
            raise ValueError("calendar place/date/time does not match the received event")
        return event

    def attendance(self, actor: Agent, minute: int):
        for entry in self.world.calendar(actor.id):
            if entry.location != actor.location or not entry.start <= minute < entry.end:
                continue
            try:
                link = self.world.get("event_rsvps", entry.id)
            except KeyError:
                continue
            event = self.world.get("gatherings", link["event_id"])
            if (
                event["active"]
                and event["location"] == actor.location
                and event["start"] <= minute < event["end"]
                and self.world.agent(event["host"]).location == actor.location
            ):
                return event
        return None
