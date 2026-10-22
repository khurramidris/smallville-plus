import json
from collections import Counter
from decimal import Decimal
from statistics import mean, pvariance
from types import SimpleNamespace

from smallville.agents.knowledge import campaign_evidence, party_schedule_evidence
from smallville.economy.metrics import evaluate_economy
from smallville.eval.protocol import evaluation_manifest
from smallville.world.models import Agent
from smallville.world.store import WorldState

PAPER = {
    "source": "https://arxiv.org/html/2304.03442v2#S7.SS1",
    "agents": 25,
    "days": 2,
    "sam_awareness": 8,
    "party_awareness": 13,
    "party_invited_guests": 12,
    "party_attending_guests": 5,
    "network_density_initial": 0.167,
    "network_density_final": 0.74,
}
ATUS = {
    "source": "https://www.bls.gov/news.release/archives/atus_06262025.htm",
    "year": 2024,
    "population": "US civilian population age 15+, all days",
    "sleep_hours": 9.04,
    "work_hours": 3.13,
    "leisure_hours": 5.07,
}


def density(agents: list[Agent]) -> float:
    edges = sum(
        b.id in a.relationships and a.id in b.relationships
        for i, a in enumerate(agents)
        for b in agents[i + 1 :]
    )
    return 2 * edges / (len(agents) * (len(agents) - 1)) if len(agents) > 1 else 0


def cost_from_events(events: list) -> dict:
    calls = [e.data for e in events if e.kind == "llm_call"]
    return {
        "calls": len(calls),
        "cache_hits": sum(c["cached"] for c in calls),
        "input_tokens": sum(c["input_tokens"] for c in calls),
        "output_tokens": sum(c["output_tokens"] for c in calls),
        "usd": str(sum((Decimal(c["usd"]) for c in calls), Decimal(0))),
        "uncertain_calls": sum(c["status"] == "uncertain" for c in calls),
        "purposes": dict(Counter(c.get("purpose", "legacy_unknown") for c in calls)),
    }


def all_events(world: WorldState):
    after = 0
    while batch := world.log.read(after=after, limit=1000):
        yield from batch
        after = batch[-1].seq


def evaluate(world: WorldState) -> dict:
    run = world.get("metadata", "run")
    config = world.get("metadata", "config")
    agents = world.agents()
    # Read only lightweight fields for metrics; retaining every full snapshot
    # would multiply memory use on expanded populations.
    events = [
        SimpleNamespace(seq=r[0], minute=r[1], kind=r[2], actor=r[3], data=json.loads(r[4]))
        for r in world.db.execute(
            "SELECT seq,minute,kind,actor,json_extract(record,'$.data') FROM events ORDER BY seq"
        )
    ]
    first = world.log.read(limit=1)[0]
    # Bootstrap can replace seed projections with phase-specific contracts in
    # the same event. Reconstruct the actual initial projection once per ID.
    initial = list(
        {c.id: Agent.model_validate(c.value) for c in first.changes if c.table == "agents"}.values()
    )
    days = run["completed_minutes"] / 1440
    denominator = len(agents) * days
    costs = cost_from_events(events)
    costs["usd_per_agent_per_simulated_day"] = (
        str(Decimal(costs["usd"]) / Decimal(str(denominator))) if denominator else None
    )
    costs["max_usd"] = config["max_usd"]
    costs["accounting"] = (
        "MockLLM has no billable tokens or USD; token counts are synthetic."
        if config["backend"] == "mock"
        else "Usage at configured conservative token rates, not a provider invoice."
    )

    def aware(agent, topic):
        if topic == "party":
            return any("valentine" in m.text.lower() for m in agent.memories)
        return any(campaign_evidence(agent.id, m.text) for m in agent.memories)

    messages = world.all("messages")
    attached_invites = {
        i["message_id"] for i in world.all("invitations") if i["event_id"] == "valentine_2023"
    }
    invitations = [
        m
        for m in messages
        if m["sent_at"] < 2460
        and (party_schedule_evidence(m["body"]) or m["id"] in attached_invites)
    ]
    invited = {m["to"] for m in invitations} - {"isabella_rodriguez"}
    read_invites = {m["to"] for m in invitations if m["read_at"] is not None} - {
        "isabella_rodriguez"
    }
    attending = {
        e.actor
        for e in events
        if e.kind == "action_completed"
        and e.data.get("kind") == "attend"
        and e.data.get("location") == "hobbs_cafe"
        and e.data["start"] < 2580
        and e.minute > 2460
        and (
            run.get("phase", 1) < 3
            or (e.data.get("event_id") == "valentine_2023" and e.data.get("attendance_confirmed"))
        )
    } - {"isabella_rodriguez"}
    per_agent = {}
    for agent in agents:
        counts = agent.activity_minutes
        divisor = max(days, 1e-9) * 60
        per_agent[agent.id] = {
            "sleep_hours": counts.get("sleep", 0) / divisor,
            "work_hours": counts.get("work", 0) / divisor,
            "leisure_hours": sum(counts.get(k, 0) for k in ("leisure", "attend", "message"))
            / divisor,
            "travel_hours": counts.get("move", 0) / divisor,
            "other_hours": sum(
                v
                for k, v in counts.items()
                if k not in ("sleep", "work", "leisure", "attend", "message", "move")
            )
            / divisor,
        }
    averages = {k: mean(v[k] for v in per_agent.values()) for k in next(iter(per_agent.values()))}
    behavior_variance = {k: pvariance(v[k] for v in per_agent.values()) for k in averages}
    knowledge = world.all("knowledge")
    campaign_records = [
        row
        for row in knowledge
        if row["predicate"] == "mayoral_candidacy"
        and row["claim_status"] in ("considering", "declared")
    ]
    memory_ids = {agent.id: {memory.id for memory in agent.memories} for agent in agents}
    campaign_interviews = [
        event.data
        for event in events
        if event.kind == "interview" and event.data.get("category") == "campaign_recall"
    ]
    cognition = [event.data.get("cognition", {}) for event in events if event.kind == "intention"]
    perceptions = [event.data for event in events if event.kind == "perceived"]
    return {
        "run": run,
        "backend": config["backend"],
        "agents": len(agents),
        "interpretation": (
            "Deterministic scripted MockLLM fixture: engineering evidence only, not realism or emergence."
            if config["backend"] == "mock"
            else f"Exploratory Phase {run.get('phase', 1)} run. No matched experimental design or human believability judgment."
        ),
        "paper_reference": PAPER,
        "evaluation_manifest": evaluation_manifest(world, config, run),
        "diffusion": {
            "sam": {
                "initial": sum(aware(a, "sam") for a in initial),
                "retained_final": sum(aware(a, "sam") for a in agents),
                "paper_final": 8,
            },
            "party": {
                "initial": sum(aware(a, "party") for a in initial),
                "retained_final": sum(aware(a, "party") for a in agents),
                "paper_final": 13,
            },
            "method": "Retained memory evidence, not omniscient delivery or unverified interview assertions.",
        },
        "knowledge_evidence": {
            "version": 1,
            "campaign": {
                "records": len(campaign_records),
                "exposed_residents": sorted({row["owner"] for row in campaign_records}),
                "accepted_belief_residents": sorted(
                    {
                        row["owner"]
                        for row in campaign_records
                        if row["epistemic_status"] == "accepted"
                    }
                ),
                "retained_evidence_residents": sorted(
                    {
                        row["owner"]
                        for row in campaign_records
                        if row["retained_memory_id"] in memory_ids.get(row["owner"], set())
                    }
                ),
                "claim_status_counts": dict(
                    Counter(row["claim_status"] for row in campaign_records)
                ),
                "interview_recall": {
                    "collected": len(campaign_interviews),
                    "human_assessed": sum(
                        row.get("claim_assessment") is not None for row in campaign_interviews
                    ),
                    "aware": None,
                },
            },
            "method": (
                "Owner-scoped structured evidence distinguishes exposure, acceptance, retained "
                "records and recall. Testimony is not world truth; unassessed interview answers "
                "do not become awareness scores. The historical diffusion metric is preserved."
            ),
        },
        "cognition_diagnostics": {
            "plans": dict(Counter(row.get("plan", "legacy_unknown") for row in cognition)),
            "actions": dict(Counter(row.get("action", "legacy_unknown") for row in cognition)),
            "reflections": dict(
                Counter(row["reflection"] for row in cognition if row.get("reflection") is not None)
            ),
            "interaction_opportunities": {
                "activations_with_someone_nearby": sum(
                    bool(row.get("nearby")) for row in perceptions
                ),
                "nearby_resident_exposures": sum(len(row.get("nearby", [])) for row in perceptions),
                "activations_with_unread_notifications": sum(
                    row.get("unread_notifications", 0) > 0 for row in perceptions
                ),
            },
            "note": "Opportunities are co-presence/notifications at activation, not proof of interaction.",
        },
        "relationships": {
            "initial_density": density(initial),
            "final_density": density(agents),
            "growth": density(agents) - density(initial),
            "definition": "Undirected edge only when both residents have relationship records; negative ties count.",
        },
        "party": {
            "invited_guests": len(invited),
            "read_invitation_guests": len(read_invites),
            "attending_guests": len(attending),
            "guest_ids": sorted(attending),
            "invited_attending_guests": len(attending & invited),
            "attendance_rate": len(attending & invited) / len(invited) if invited else None,
            "paper_attendance_rate": 5 / 12,
            "window": {"location": "hobbs_cafe", "start": 2460, "end": 2580},
            "method": "Completed attend actions overlapping the party window; host excluded.",
        },
        "anti_homogeneity": {
            "seeded_opinion_variance": pvariance(a.persona.opinion for a in agents),
            "observed_daily_behavior_variance": behavior_variance,
            "note": "Opinion values are synthetic heterogeneous priors; survey fidelity is not measured.",
        },
        "daily_life": {
            "average_hours": averages,
            "per_agent": per_agent,
            "atus_reference": ATUS,
            "difference_hours": {
                k: averages[k] - ATUS[k] for k in ("sleep_hours", "work_hours", "leisure_hours")
            },
            "note": "Shape diagnostic only. Smallville occupations/age mix and two weekdays differ from ATUS. "
            "Study is grouped with work; leisure includes messages; travel is separate. No calibration claim.",
        },
        "cost": costs,
        "messages": sum(m["sent_at"] >= 0 for m in messages),
        "historical_messages": sum(m["sent_at"] < 0 for m in messages),
        "economy": evaluate_economy(world, events) if run.get("phase") == 3 else {"enabled": False},
        "rejected_actions": dict(
            Counter(e.data["reason"] for e in events if e.kind == "action_rejected")
        ),
        "interviews": {
            "responses": sum(e.kind == "interview" for e in events),
            "human_believability_score": None,
            "note": "Run the interview command and collect blinded human ratings; no automatic score is fabricated.",
        },
    }
