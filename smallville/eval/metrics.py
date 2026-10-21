from collections import Counter
from decimal import Decimal
from statistics import mean, pvariance

from smallville.agents.knowledge import campaign_evidence
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
    events = list(all_events(world))
    first = next(e for e in events if e.kind == "initialized")
    initial = [Agent.model_validate(c.value) for c in first.changes if c.table == "agents"]
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
    invitations = [
        m
        for m in messages
        if m["sent_at"] < 2460
        and "valentine" in m["body"].lower()
        and "hobbs" in m["body"].lower()
        and ("17:00" in m["body"] or "5pm" in m["body"].lower())
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
    return {
        "run": run,
        "backend": config["backend"],
        "agents": len(agents),
        "interpretation": (
            "Deterministic scripted MockLLM fixture: engineering evidence only, not realism or emergence."
            if config["backend"] == "mock"
            else "Exploratory Phase 1 run. No matched experimental design or human believability judgment."
        ),
        "paper_reference": PAPER,
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
        "messages": len(messages),
        "rejected_actions": dict(
            Counter(e.data["reason"] for e in events if e.kind == "action_rejected")
        ),
        "interviews": {
            "responses": sum(e.kind == "interview" for e in events),
            "human_believability_score": None,
            "note": "Run the interview command and collect blinded human ratings; no automatic score is fabricated.",
        },
    }
