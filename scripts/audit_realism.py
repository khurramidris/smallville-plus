"""Read-only diagnostics of an existing run; performs no inference or network IO.

Run: python scripts/audit_realism.py --run runs/phase3-resumed-live-25 \
    --out reports/realism/phase3-audit.json
"""

import argparse
import hashlib
import json
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from smallville.agents.drives import advance_drives, conversation_effect  # noqa: E402
from smallville.agents.knowledge import campaign_evidence  # noqa: E402
from smallville.world.models import Agent  # noqa: E402


def open_readonly(path):
    return sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)


def memory_key(memory):
    return memory["id"], memory["minute"], memory["source"], memory["text"]


def response_type(content):
    try:
        value = json.loads(content)
    except (TypeError, ValueError):
        return "invalid_json"
    if not isinstance(value, dict):
        return "other"
    for field, label in (
        ("blocks", "plan"),
        ("kind", "action"),
        ("evidence", "reflection"),
        ("plausible", "adjudication"),
    ):
        if field in value:
            return label
    return "other"


def heuristic_probes(raw):
    cases = []
    for utterance in (
        "I do not disagree with you.",
        "No thanks, I am upset about what you did.",
    ):
        actor = Agent.model_validate(raw)
        prior = actor.relationships.get("audit_peer", 0)
        conversation_effect(actor, "audit_peer", utterance)
        emotion = actor.emotion.model_dump()
        delta = actor.relationships["audit_peer"] - prior
        advance_drives(actor, actor.updated_at)
        cases.append(
            {
                "utterance": utterance,
                "relationship_delta": delta,
                "emotion_after_message": emotion,
                "emotion_after_zero_elapsed_drive_update": actor.emotion.model_dump(),
            }
        )
    return {
        "method": "Isolated resident copies; no world writes. Illustrative counterexamples, not calibrated psychology.",
        "cases": cases,
    }


def audit(directory):
    with (
        open_readonly(directory / "world.sqlite3") as db,
        open_readonly(directory / "cache.sqlite3") as cache,
    ):
        db.execute("BEGIN")
        metadata = {key: json.loads(raw) for key, raw in db.execute("SELECT id,data FROM metadata")}
        assert metadata["run"]["status"] == "completed"
        final = {key: json.loads(raw) for key, raw in db.execute("SELECT id,data FROM agents")}
        current, initial, seen, first_seed_loss = {}, {}, set(), {}
        new_memory_sources = Counter()
        calls, intentions, completions, sources = Counter(), Counter(), Counter(), Counter()
        ever_campaign, calls_by_agent = set(), Counter()
        social_text_examples, attempts = [], []
        first_campaign_loss = {}
        final_seq = 0
        for seq, record in db.execute("SELECT seq,record FROM events ORDER BY seq"):
            event = json.loads(record)
            final_seq = seq
            # Last update per resident wins within an atomic initialization event.
            updates = {c["id"]: c["value"] for c in event["changes"] if c["table"] == "agents"}
            for identifier, actor in updates.items():
                previous = current.get(identifier)
                if (
                    previous
                    and any(campaign_evidence(identifier, m["text"]) for m in previous["memories"])
                    and not any(campaign_evidence(identifier, m["text"]) for m in actor["memories"])
                ):
                    first_campaign_loss.setdefault(identifier, event["minute"])
                current[identifier] = actor
                if event["kind"] == "initialized":
                    initial[identifier] = actor
                keys = {memory_key(m) for m in actor["memories"]}
                for m in actor["memories"]:
                    identity = (identifier, memory_key(m))
                    if identity not in seen:
                        new_memory_sources[m["source"].split(":")[0]] += 1
                        seen.add(identity)
                    if campaign_evidence(identifier, m["text"]):
                        ever_campaign.add(identifier)
                seed_keys = {
                    memory_key(m)
                    for m in initial[identifier]["memories"]
                    if m["source"] == "original_seed"
                }
                if seed_keys - keys and identifier not in first_seed_loss:
                    first_seed_loss[identifier] = event["minute"]
            data = event["data"]
            if event["kind"] == "llm_call":
                row = cache.execute(
                    "SELECT content FROM responses WHERE model=? AND prompt_hash=? AND seed=?",
                    (data["model"], data["prompt_hash"], data["seed"]),
                ).fetchone()
                assert row is not None, "successful call has no cached response"
                calls[response_type(row[0])] += 1
                calls_by_agent[event["actor"]] += 1
            elif event["kind"] == "intention":
                intentions[data["intent"]["kind"]] += 1
                sources[data.get("source", "model")] += 1
                intent = data["intent"]
                if intent["kind"] in ("leisure", "attempt") and re.search(
                    r"\b(talk|chat|conversation|discuss|greet)\b", intent["text"], re.I
                ):
                    if len(social_text_examples) < 5:
                        social_text_examples.append(
                            {
                                "minute": event["minute"],
                                "actor": event["actor"],
                                "kind": intent["kind"],
                                "intention_text": intent["text"],
                                "note": "Intention wording does not establish a conversation.",
                            }
                        )
            elif event["kind"] == "action_completed":
                completions[data["kind"]] += 1
                if data["kind"] == "attempt":
                    attempts.append(
                        {
                            "minute": event["minute"],
                            "actor": event["actor"],
                            "observations": event["observations"],
                            "changed_tables": sorted({c["table"] for c in event["changes"]}),
                        }
                    )
        assert current == final, "event snapshots do not match final projections"
        final_sources = Counter(
            m["source"].split(":")[0] for a in final.values() for m in a["memories"]
        )
        initial_seed_count = sum(
            m["source"] == "original_seed" for a in initial.values() for m in a["memories"]
        )
        messages = [json.loads(row[0]) for row in db.execute("SELECT data FROM messages")]
        campaign_messages = []
        for message in sorted(messages, key=lambda m: (m["sent_at"], m["id"])):
            if re.search(r"mayor|campaign|election|candidacy", message["body"], re.I):
                text = f"{message['sender']} told me: {message['body']}"
                campaign_messages.append(
                    {
                        **{
                            k: message[k]
                            for k in ("id", "sender", "to", "body", "sent_at", "read_at")
                        },
                        "narrow_metric_recognizes_recipient_memory": campaign_evidence(
                            message["to"], text
                        ),
                        "retained_in_recipient_memories": any(
                            m["source"] == message["id"] for m in final[message["to"]]["memories"]
                        ),
                    }
                )
        cfg = metadata["config"]
        report = json.loads((directory / "report.json").read_text())
        with (directory / "events.jsonl").open("rb") as file:
            event_hash = hashlib.file_digest(file, "sha256").hexdigest()
        return {
            "source_run": str(directory),
            "run": metadata["run"],
            "event_count": final_seq,
            "event_log_sha256": event_hash,
            "event_projection_check": "passed",
            "method": "Read-only recorded events, final projections and exact response cache; no inference.",
            "limits": [
                "Single exploratory seed/model; descriptive findings do not isolate causal effects.",
                "Campaign detection reuses the existing narrow phrase-based metric, not semantic understanding.",
                "Response types are classified by JSON fields; this does not validate response quality.",
                "Unique memory counts use id/minute/source/text to avoid snapshot duplication.",
            ],
            "cohort": {
                "residents": len(final),
                "with_life_history": sum(
                    bool(a["persona"]["life_history"]) for a in initial.values()
                ),
                "historical_messages": sum(m["sent_at"] < 0 for m in messages),
                "population_artifact_present": "population" in metadata,
                "tiers": dict(Counter(a["persona"]["tier"] for a in initial.values())),
                "models": {
                    k: cfg[k]
                    for k in (
                        "model_deep",
                        "model_fast",
                        "model_gm",
                        "embed_model",
                        "model_overrides",
                    )
                },
            },
            "behavior": {
                "intentions": dict(sorted(intentions.items())),
                "completed_actions": dict(sorted(completions.items())),
                "intention_sources": dict(sources),
                "live_messages": sum(m["sent_at"] >= 0 for m in messages),
                "message_dyads": len(
                    {tuple(sorted((m["sender"], m["to"]))) for m in messages if m["sent_at"] >= 0}
                ),
                "social_text_examples": social_text_examples,
                "attempt_completion_examples": attempts[:3],
                "attempts_modifying_only_actor_table": sum(
                    a["changed_tables"] == ["agents"] for a in attempts
                ),
            },
            "memory": {
                "final_lengths": dict(
                    sorted(Counter(len(a["memories"]) for a in final.values()).items())
                ),
                "original_seed_entries_initial": initial_seed_count,
                "original_seed_entries_final": final_sources["original_seed"],
                "agents_losing_at_least_one_original_seed": len(first_seed_loss),
                "first_original_seed_eviction_minute_by_agent": first_seed_loss,
                "sam_first_original_seed_eviction_minute": first_seed_loss.get("sam_moore"),
                "ever_detected_campaign_evidence": sorted(ever_campaign),
                "first_detected_campaign_loss_minute": first_campaign_loss,
                "retained_campaign_evidence": sorted(
                    key
                    for key, a in final.items()
                    if any(campaign_evidence(key, m["text"]) for m in a["memories"])
                ),
                "unique_memory_sources_over_run": dict(sorted(new_memory_sources.items())),
                "final_memory_sources": dict(sorted(final_sources.items())),
            },
            "inference": {
                "successful_response_types": dict(calls),
                "responses_per_resident_day": sum(calls.values())
                / (len(final) * metadata["run"]["completed_minutes"] / 1440),
                "responses_by_agent": dict(sorted(calls_by_agent.items())),
                "whole_experiment_cost": report["whole_experiment_cost"],
            },
            "existing_metrics": {
                key: report[key]
                for key in ("diffusion", "relationships", "party", "rejected_actions", "interviews")
            },
            "campaign_message_review": {
                "note": "Topic matches are review candidates, not proof of awareness. Distinguish considering a candidacy from declaring one. The Sam/Adam exchange exposes phrase/attribution limitations in the current scorer.",
                "messages": campaign_messages,
            },
            "heuristic_probes": heuristic_probes(final[sorted(final)[0]]),
            "additional_provider_calls": 0,
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.run)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {"artifact": str(args.out), "events": result["event_count"], "provider_calls": 0}
        )
    )


if __name__ == "__main__":
    main()
