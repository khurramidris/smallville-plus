"""Versioned, key-free evaluation metadata for comparable research runs."""

BASE_PROTOCOL_VERSION = "realism-eval-v1"
CONNECTED_PROTOCOL_VERSION = "realism-eval-v2"


def evaluation_manifest(world, config: dict, run: dict) -> dict:
    try:
        population = world.get("metadata", "population")
    except KeyError:
        population = None
    connected = config.get("realism_profile") == "connected_v1"
    measurement = {
        "legacy_diffusion": "retained phrase evidence; preserved for historical comparison",
        "structured_knowledge": "owner-scoped exposure/acceptance/retention/recall stages",
        "interview_recall": "reported only after human claim assessment",
        "memory_retrieval": "owner-scoped bounded working/archive lexical ranking",
        "goal_lifecycle": "current projection plus immutable validated transitions",
        "plan_repair": "future-only patch; elapsed plan blocks remain unchanged",
        "relationship_density": "mutual recorded relationship edges",
        "attendance": "completed and confirmed event actions",
    }
    if connected:
        measurement.update(
            social_scenes=(
                "app proposals, independent final invitation states, admitted participants and "
                "listener-scoped committed turns"
            ),
            phone_attention=(
                "explicit five-minute checks, messages read by those checks and unread remainder"
            ),
            directed_relationships=(
                "owner-to-peer trust, affinity, familiarity and obligation; signed changes cite "
                "witnessed turns"
            ),
        )
    return {
        "protocol_version": (CONNECTED_PROTOCOL_VERSION if connected else BASE_PROTOCOL_VERSION),
        "seed": config["seed"],
        "backend": config["backend"],
        "models": {
            "deep": config["model_deep"],
            "fast": config["model_fast"],
            "gm": config["model_gm"],
            "embedding": config["embed_model"],
            "overrides": config["model_overrides"],
        },
        "realism_profile": config.get("realism_profile", "baseline"),
        "population": (
            {
                "kind": "validated_artifact",
                "digest": population["digest"],
                "version": population.get("version", 2),
                "residents": population["residents"],
                "history_days": population["history_days"],
            }
            if population
            else {"kind": "original_25_seed_workflow", "digest": None, "residents": 25}
        ),
        "horizon_minutes": run["completed_minutes"],
        "benchmark": run.get("benchmark"),
        "measurement": measurement,
        "claim_boundary": (
            "This manifest enables comparison but does not make runs independent, matched to the "
            "original paper, or human-validated. Cached reruns are not replications."
        ),
    }
