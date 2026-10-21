from collections import Counter

from smallville.world.store import WorldState


def evaluate_economy(world: WorldState, events: list) -> dict:
    metadata = world.get("metadata", "economy")
    accounts, transfers = world.all("accounts"), world.all("transfers")
    first = world.log.read(limit=1)[0]
    reconstructed = {c.id: c.value["cents"] for c in first.changes if c.table == "accounts"}
    for row in transfers:
        reconstructed[row["source"]] -= row["cents"]
        reconstructed[row["destination"]] += row["cents"]
    mismatch = [a["id"] for a in accounts if reconstructed[a["id"]] != a["cents"]]
    consumed = sum(e.data.get("meals_consumed", 0) for e in events if e.kind == "action_completed")
    food = (
        sum(i["meals"] for i in world.all("inventories"))
        + sum(s["stock"] for s in world.all("shops"))
        + world.get("objects", "wholesale_meals")["units"]
    )
    purposes = Counter()
    for row in transfers:
        purposes[row["purpose"]] += row["cents"]
    leases, jobs, agents = world.all("leases"), world.all("jobs"), world.agents()
    return {
        "enabled": True,
        "units": "fictional town cents and meal units, separate from API USD",
        "assumptions": metadata,
        "audit": {
            "initial_cents": metadata["initial_cents"],
            "final_cents": sum(a["cents"] for a in accounts),
            "money_conserved": sum(a["cents"] for a in accounts) == metadata["initial_cents"],
            "ledger_matches_accounts": not mismatch,
            "mismatched_accounts": mismatch,
            "nonnegative_accounts": all(a["cents"] >= 0 for a in accounts),
            "initial_meals": metadata["initial_meals"],
            "remaining_meals": food,
            "consumed_meals": consumed,
            "food_conserved": food + consumed == metadata["initial_meals"],
            "work_limits_respected": all(
                all(m <= j["max_daily_minutes"] for m in j["worked_minutes"].values()) for j in jobs
            ),
        },
        "transfers": len(transfers),
        "flows_cents": dict(purposes),
        "rent_arrears_cents": sum(lease["arrears_cents"] for lease in leases),
        "residents_in_arrears": sum(lease["arrears_cents"] > 0 for lease in leases),
        "unpaid_wages_cents": sum(j["unpaid_cents"] for j in jobs),
        "shops": world.all("shops"),
        "resource_pressure": {
            "residents_without_meals": sum(
                world.get("inventories", a.id)["meals"] == 0 for a in agents
            ),
            "hungry_without_meals": sum(
                a.needs.fullness < 25 and world.get("inventories", a.id)["meals"] == 0
                for a in agents
            ),
            "failed_purchases": sum(
                (
                    e.kind == "action_completed"
                    and e.data.get("kind") == "buy"
                    and not e.data.get("succeeded", True)
                )
                or (e.kind == "action_rejected" and "purchase" in e.data["reason"])
                for e in events
            ),
            "delayed_delivery_days": [
                e.data["day"]
                for e in events
                if e.kind == "shops_restocked" and e.data["delivery_delayed"]
            ],
        },
        "council": [
            {k: v for k, v in p.items() if k != "electorate"} for p in world.all("proposals")
        ],
        "ballots": len(world.all("ballots")),
        "news": {
            "published": len(world.all("news")),
            "residents_reading": len(world.all("news_reads")),
        },
        "note": "Scenario rates, support transfers and freelance demand are authored assumptions; "
        "this is not a calibrated economy or a validated model of political behavior.",
    }
