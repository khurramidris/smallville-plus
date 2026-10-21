"""Compile reciprocal, private phone histories before the simulation epoch."""

import re
from collections import defaultdict
from string import Formatter

from pydantic import Field, model_validator

from smallville.agents.memory import remember
from smallville.world.models import Agent, CalendarEntry, Message, Model


class HistoryTemplates(Model):
    openings: list[str] = Field(min_length=3, max_length=8)
    replies: list[str] = Field(min_length=3, max_length=8)

    @model_validator(mode="after")
    def grounded_templates(self):
        for text in [*self.openings, *self.replies]:
            if not 10 <= len(text) <= 400:
                raise ValueError("history messages must be short natural-language templates")
            if re.search(
                r"valentine|party|mayor|election|simulation|simulated|AI assistant", text, re.I
            ):
                raise ValueError("history template leaks future benchmark news or self-awareness")
            for _, field, spec, conversion in Formatter().parse(text):
                if field is not None and (
                    field not in {"sender_name", "recipient_name", "interest"} or spec or conversion
                ):
                    raise ValueError("unknown history template placeholder")
        return self


def mock_history(context: dict) -> dict:
    if "blunt" in context["style"] or "reserved" in context["style"]:
        return {
            "openings": [
                "Any time for a short walk, {recipient_name}?",
                "I made a little progress with {interest}. Still plenty to do.",
                "Busy day. Checking in before I get back to my own work.",
            ],
            "replies": [
                "Not today. I need some time to myself.",
                "I can spare a little time later. Send a message first.",
                "I hear you. I've been occupied with my own responsibilities.",
            ],
        }
    return {
        "openings": [
            "Hi {recipient_name}, have you had a chance to take a break?",
            "I spent some time on {interest} today. How has your day been?",
            "I've been balancing my responsibilities with a little time to myself.",
        ],
        "replies": [
            "I have a few things to finish, so I can't join you today.",
            "A short catch-up would be good. Let's make time when we are both free.",
            "Thanks for checking in. I am keeping my own plans for the evening.",
        ],
    }


def compile_histories(
    agents: list[Agent], templates: dict[str, HistoryTemplates], days: int
) -> tuple[list[Message], list[CalendarEntry]]:
    if not 14 <= days <= 60:
        raise ValueError("digital history must cover 14 to 60 prior calendar days")
    by_id = {a.id: a for a in agents}
    messages, calendar = [], []
    # A ring creates a small connected acquaintance network. Existing source
    # relationships (including negative ones) are retained, not overwritten.
    for index, actor in enumerate(agents):
        peer = agents[(index + 1) % len(agents)]
        for a, b in ((actor, peer), (peer, actor)):
            if b.id not in a.contacts:
                a.contacts.append(b.id)
            a.relationships.setdefault(b.id, 0.15)
        for day in range(-days, 0):
            sent = day * 1440 + 840 + index % 120
            interest = actor.persona.life_history.interests[(day + index) % 2]
            opening = templates[actor.id].openings[
                (day + index) % len(templates[actor.id].openings)
            ]
            reply = templates[peer.id].replies[(day + index) % len(templates[peer.id].replies)]
            for offset, sender, recipient, text in (
                (0, actor, peer, opening),
                (7, peer, actor, reply),
            ):
                identifier = f"history:message:{index}:{day}:{offset}"
                unread = day == -1 and (index + offset) % 10 == 0
                messages.append(
                    Message(
                        id=identifier,
                        sender=sender.id,
                        to=recipient.id,
                        body=text.format(
                            sender_name=sender.persona.name,
                            recipient_name=recipient.persona.name,
                            interest=interest,
                        ),
                        sent_at=sent + offset,
                        read_at=None if unread else sent + offset + 3,
                    )
                )
    venues = ("johnson_park", "hobbs_cafe", "oak_hill_college")
    for week in range(days // 7):
        day = -days + week * 7 + 5  # Saturday before the Monday epoch.
        if day >= 0:
            continue
        for index in range(0, len(agents), 2):
            participants = agents[index : index + 2]
            location = (
                venues[(index // 2) % len(venues)]
                if len(participants) == 2
                else participants[0].persona.home
            )
            for actor in participants:
                calendar.append(
                    CalendarEntry(
                        id=f"history:calendar:{week}:{index}:{actor.id}",
                        owner=actor.id,
                        title="A short catch-up"
                        if len(participants) == 2
                        else "Time for my interests",
                        start=day * 1440 + 600,
                        end=day * 1440 + 630,
                        location=location,
                        attendees=[a.id for a in participants],
                    )
                )
    read_by_owner = defaultdict(list)
    for message in sorted(messages, key=lambda m: (m.sent_at, m.id)):
        if message.read_at is not None:
            read_by_owner[message.to].append(message)
    for actor in agents:
        remember(
            actor,
            0,
            "I have kept in touch with the people in my contacts over the past few weeks.",
            "digital_history",
            0.35,
            "seed",
        )
        for message in read_by_owner[actor.id][-3:]:
            remember(
                actor, message.read_at, f"{message.sender} told me: {message.body}", message.id, 0.4
            )
        actor.contacts.sort()
    assert all(m.sender in by_id and m.to in by_id for m in messages)
    return messages, calendar
