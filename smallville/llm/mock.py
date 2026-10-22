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
    if p["id"] == "sam_moore" or any(
        word in p.get("work_status", "").lower()
        for word in ("retired", "unemployed", "keeping house")
    ):
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

    social = context.get("conversation_app")
    if social:
        if social["pending_invitations"]:
            invitation = social["pending_invitations"][0]
            relationship = context["relationship_states"].get(invitation["from"], {})
            willing = invitation["can_accept"] and relationship.get("trust", 0) >= -0.1
            return intend(
                "conversation_respond",
                duration=5,
                arguments={
                    "conversation_id": invitation["id"],
                    "response": "accept" if willing else "refuse",
                    "reason": (
                        "I have room in my plans and am willing to hear them out."
                        if willing
                        else invitation["constraint"]
                        or "I do not trust this conversation enough to give it my time."
                    ),
                },
                text="I want to answer the conversation invitation for myself.",
            )
        for scene in social["commitments"]:
            travel = context["travel_minutes"].get(scene["location"], 10**6)
            if scene["start"] - travel <= minute < scene["start"]:
                return go_or("wait", scene["location"], max(1, scene["start"] - minute))
        notifications = context["perception"]["notifications"]
        last_checked = context["phone_attention"]["last_checked"]
        if notifications and (
            any(item["verbosity"] == "urgent" for item in notifications)
            or last_checked < minute - 90
        ):
            return intend(
                "check_phone",
                duration=5,
                text="I want to spend a few minutes checking some messages.",
            )
        can_host = "conversation_invite" in context.get("known_feasible_actions", [])
        nearby = sorted(peer["id"] for peer in context["perception"]["nearby"])
        if (
            can_host
            and nearby
            and social["hosted_today"] == 0
            and block["activity"] == "leisure"
            and 600 <= hour < 1200
        ):
            start = minute + 15
            end = start + 20
            hours = context["opening_hours"][here]
            local_end = end % 1440
            stays_open = hours["opens"] == 0 and hours["closes"] == 1440
            stays_open = stays_open or hours["opens"] <= hour < local_end <= hours["closes"]
            if stays_open:
                topic = (
                    context["active_goals"][0]["description"][:180]
                    if context["active_goals"]
                    else "how our current plans are going"
                )
                return intend(
                    "conversation_invite",
                    duration=5,
                    arguments={
                        "participants": nearby[:2],
                        "topic": topic,
                        "start": start,
                        "end": end,
                        "location": here,
                    },
                    text="I want to ask the people here whether they want to talk.",
                )

    if context.get("phase") == 3 and block["activity"] != "sleep":
        from smallville.llm.mock_economy import economic_action

        if chosen := economic_action(context, intend):
            return chosen
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
                **(
                    {"event_id": "valentine_2023"}
                    if context.get("phase") == 3
                    and any(e["id"] == "valentine_2023" for e in context["shared_events"])
                    else {}
                ),
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
                    arguments={
                        "to": recipient,
                        "body": body,
                        **(
                            {"event_id": "valentine_2023"}
                            if context.get("phase") == 3
                            and topic == "Valentine"
                            and any(e["id"] == "valentine_2023" for e in context["shared_events"])
                            else {}
                        ),
                    },
                    text=f"I want to message {recipient}.",
                )
    destination = block["location"]
    duration = min(60, block["end"] - hour)
    if context.get("phase") == 3 and block["activity"] == "work":
        job = context["economy"]["job"]
        used = job["worked_minutes"].get(str(day), 0)
        if (
            job["kind"] == "none"
            or hour < job["shift_start"]
            or hour >= job["shift_end"]
            or used >= job["max_daily_minutes"]
        ):
            return intend("leisure", duration=duration)
        duration = min(duration, job["shift_end"] - hour, job["max_daily_minutes"] - used)
    hours = context["opening_hours"].get(destination, {"opens": 0, "closes": 1440})
    arrival_hour = hour + context["travel_minutes"].get(destination, 0)
    if not hours["opens"] <= arrival_hour < hours["closes"]:
        return go_or("leisure", home, duration)
    if here == destination:
        duration = min(duration, hours["closes"] - hour)
    if block["activity"] == "eat" and needs["fullness"] >= 65:
        return intend("leisure", duration=duration)
    return go_or(block["activity"], destination, duration)


def conversation_turn(context: dict, seed: int) -> dict:
    private = context["private_conversation"]
    conversation = private["conversation"]
    turns = private["turns"]
    actor = context["self"]["id"]
    if min(context["needs"]["energy"], context["needs"]["fullness"]) < 20:
        return {
            "action": "leave",
            "text": "I need to look after myself, so I am leaving now.",
            "appraisals": [],
        }
    if turns and len(turns) >= len(conversation["turn_order"]) + 1:
        digest = int(hashlib.sha256(f"{actor}:{conversation['id']}".encode()).hexdigest()[:4], 16)
        if digest % 4 == 0:
            return {
                "action": "leave",
                "text": "I have said what I needed to say and am returning to my plans.",
                "appraisals": [],
            }
    if not turns:
        text = f"I wanted to hear your own views about {conversation['topic']}."
        appraisals = []
    else:
        last = turns[-1]
        peer = last["speaker"]
        digest = int(
            hashlib.sha256(f"{actor}:{peer}:{last['id']}:{seed}".encode()).hexdigest()[:4],
            16,
        )
        stance = digest % 3 - 1
        if stance > 0:
            text = "That sounds useful to me, though I want to think through the details myself."
        elif stance < 0:
            text = "I do not see it the same way, and I am keeping my own priorities in mind."
        else:
            text = "I heard what you said. I do not have enough evidence to agree or disagree yet."
        appraisals = (
            [
                {
                    "peer": peer,
                    "trust_delta": 0.03 * stance,
                    "affinity_delta": 0.02 * stance,
                    "obligation_delta": 0,
                    "reason": (
                        "Their actual turn made me more receptive."
                        if stance > 0
                        else "Their actual turn made me more cautious."
                    ),
                    "evidence": [last["id"]],
                }
            ]
            if stance
            else []
        )
    return {"action": "speak", "text": text, "appraisals": appraisals}


class MockLLM:
    async def complete(self, *, model, prompt, seed, temperature, max_tokens):
        context = json.loads(prompt.rsplit("\n\nCURRENT CONTEXT:\n", 1)[1])
        task = context["task"]
        if task == "plan":
            result = routine(context)
        elif task == "repair_plan":
            from smallville.agents.planning import deterministic_patch

            result = deterministic_patch(context).model_dump()
        elif task == "action":
            result = action(context, seed)
        elif task == "conversation_turn":
            result = conversation_turn(context, seed)
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
        elif task == "persona":
            from smallville.personas.generation import mock_life_history

            result = mock_life_history(context, seed)
        elif task == "history_templates":
            from smallville.personas.histories import mock_history

            result = mock_history(context)
        elif task == "survey":
            from smallville.eval.surveys import mock_survey

            result = mock_survey(context, seed)
        else:
            raise ValueError("unsupported mock task")
        content = canonical(result)
        return Completion(content, len(prompt.encode()) // 4 + 1, len(content.encode()) // 4 + 1)
