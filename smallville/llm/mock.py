"""Deterministic behavioral fixture, explicitly not an emergent-agent model."""

import hashlib
import json

from smallville.agents.knowledge import campaign_evidence, party_schedule_evidence
from smallville.engine.events import canonical
from smallville.llm.gateway import Completion


def routine(context: dict) -> dict:
    p, day = context["self"], context["minute"] // 1440
    home, work = p["home"], p["workplace"]
    wake = 360 + (int(hashlib.sha256(p["id"].encode()).hexdigest()[:4], 16) % 3) * 30
    leisure = context.get("leisure_location", home)
    blocks = [
        (0, wake, "sleep", home),
        (wake, 480, "eat", home),
        (480, 540, "leisure", home),
        (540, 720, "work", work),
        (720, 780, "eat", home),
        (780, 1020, "work", work),
        (1020, 1320, "leisure", leisure),
        (1320, 1440, "sleep", home),
    ]
    if p["id"] == "arthur_burton":
        blocks = [
            (0, wake, "sleep", home),
            (wake, 480, "eat", home),
            (480, 720, "leisure", home),
            (720, 780, "eat", home),
            (780, 1020, "leisure", leisure),
            (1020, 1320, "work", work),
            (1320, 1440, "sleep", home),
        ]
    elif p["id"] == "isabella_rodriguez":
        blocks = [
            (0, wake, "sleep", home),
            (wake, 480, "eat", home),
            (480, 720, "work", work),
            (720, 780, "eat", home),
            (780, 1200, "work", work),
            (1200, 1320, "leisure", home),
            (1320, 1440, "sleep", home),
        ]
    if p["id"] == "sam_moore":
        blocks = [(s, e, "leisure" if a == "work" else a, loc) for s, e, a, loc in blocks]
    return {
        "day": day,
        "blocks": [
            {"start": s, "end": e, "activity": a, "location": loc} for s, e, a, loc in blocks
        ],
    }


def action(context: dict, seed: int) -> dict:
    p, minute = context["self"], context["minute"]
    home, here = p["home"], context["perception"]["location"]
    hour, day = minute % 1440, minute // 1440
    block = context["hour_plan"]
    needs = context["needs"]

    def intend(kind, target=None, duration=60, arguments=None, text=None):
        return {
            "kind": kind,
            "target": target,
            "duration": max(1, min(480, duration)),
            "arguments": arguments or {},
            "text": text or f"I want to {kind}.",
        }

    def go_or(kind, location, duration=60):
        if here != location:
            return intend("move", location, text=f"I want to walk to {location}.")
        return intend(kind, duration=duration)

    # Calendar entries are private intentions. There is no global guest list
    # supplied to this fixture or automatic attendance in the engine.
    for event in context["calendar"]:
        travel = context["travel_minutes"].get(event["location"], 30)
        if event["start"] - travel <= minute < event["end"]:
            return go_or("attend", event["location"], min(60, event["end"] - minute))
    if block["activity"] == "sleep":
        return go_or("sleep", home, min(480, block["end"] - hour))
    if needs["fullness"] < 38:
        return go_or("eat", home, 30)
    if needs["energy"] < 15:
        return go_or("sleep", home, 120)

    knows_campaign = any(campaign_evidence(p["id"], m["text"]) for m in context["memories"])
    knows_schedule = any(party_schedule_evidence(m["text"]) for m in context["memories"])
    # Benchmark-specific behavior lives only in MockLLM. It never changes world
    # state; the same output must pass GM checks as an actual model response.
    if (
        knows_schedule
        and minute < 2460 - 60
        and (p["sociability"] >= 0.35 or p["id"] == "isabella_rodriguez")
        and not any("valentine" in e["title"].lower() for e in context["calendar"])
    ):
        return intend(
            "calendar",
            duration=5,
            arguments={
                "title": "Valentine's party",
                "start": 2460,
                "end": 2580,
                "location": "hobbs_cafe",
            },
            text="I want to put the Valentine's party on my calendar.",
        )
    sent = context["sent"]
    today = [m for m in sent if m["sent_at"] // 1440 == day]
    quota = 8 if p["id"] in ("isabella_rodriguez", "sam_moore") else 3
    if minute - context["last_social_at"] >= 90 and len(today) < quota and 480 <= hour < 1260:
        peers = [x["id"] for x in context["perception"]["nearby"]]
        contacts = sorted(set([*p["contacts"], *peers]) - {p["id"]})
        topics = []
        if knows_schedule and minute < 2460:
            topics.append(
                (
                    "Valentine",
                    "Valentine's party at Hobbs Cafe on February 14, 17:00-19:00. Want to come?",
                )
            )
        if knows_campaign:
            topics.append(("mayor", "Sam Moore is running for mayor. I'm still making up my mind."))
        topics.append(("hello", "hello — how is your day going?"))
        for topic, body in topics:
            available = [
                c
                for c in contacts
                if not any(m["to"] == c and topic.lower() in m["body"].lower() for m in sent)
            ]
            if available:
                recipient = available[seed % len(available)]
                if topic == "Valentine" and p["sociability"] < 0.35:
                    body = "I can't make the Valentine's party; I have my own plans."
                elif topic == "mayor" and p["opinion"] < 0:
                    body = "Sam Moore is running for mayor, but I disagree with him."
                return intend(
                    "message",
                    arguments={"to": recipient, "body": body},
                    text=f"I want to message {recipient}.",
                )
    destination = block["location"]
    duration = min(60, block["end"] - hour)
    hours = context["opening_hours"].get(destination, {"opens": 0, "closes": 1440})
    arrival_hour = hour + context["travel_minutes"].get(destination, 0)
    if not hours["opens"] <= arrival_hour < hours["closes"]:
        return go_or("leisure", home, duration)
    if here == destination:
        duration = min(duration, hours["closes"] - hour)
    if block["activity"] == "eat" and needs["fullness"] >= 65:
        return intend("leisure", duration=duration)
    return go_or(block["activity"], destination, duration)


class MockLLM:
    async def complete(self, *, model, prompt, seed, temperature, max_tokens):
        context = json.loads(prompt.rsplit("\n\nCURRENT CONTEXT:\n", 1)[1])
        task = context["task"]
        if task == "plan":
            result = routine(context)
        elif task == "action":
            result = action(context, seed)
        elif task == "reflection":
            recalled = context["memories"][:3]
            result = {
                "text": "I have been balancing my own routines with the people I heard from today.",
                "evidence": [m["id"] for m in recalled],
            }
        elif task == "adjudicate":
            result = {"plausible": "impossible" not in context["intent"]["text"].lower()}
        elif task == "interview":
            recalled = context["memories"][:2]
            result = {
                "answer": "I recall: " + " ".join(m["text"] for m in recalled)
                if recalled
                else "I don't remember enough to answer.",
                "opinion": context["self"]["opinion"],
            }
        else:
            raise ValueError("unsupported mock task")
        content = canonical(result)
        return Completion(content, len(prompt.encode()) // 4 + 1, len(content.encode()) // 4 + 1)
