from __future__ import annotations

import hashlib
from collections import Counter

from smallville.agents.memory import remember
from smallville.config import Config
from smallville.economy.ledger import LedgerBatch
from smallville.economy.models import Job, Lease, Purchase, Shop
from smallville.world.models import Agent, change
from smallville.world.store import WorldState


def contract(agent: Agent) -> Job:
    p = agent.persona
    status = str(p.facts.get("work_status", "")).lower()
    text = (status + " " + p.description).lower()
    kind, allowance = "employment", 0
    if "retired" in text or agent.id == "sam_moore":
        kind, allowance = "none", 5000
    elif any(word in status for word in ("unemployed", "keeping house")):
        kind, allowance = "none", 2000
    elif "student" in text:
        kind, allowance = "study", 3500
    elif p.home == p.workplace:
        kind = "freelance"
    start, end = (1020, 1320) if agent.id == "arthur_burton" else (540, 1020)
    if agent.id == "isabella_rodriguez":
        start, end = 480, 1200
    wage = 2200 if p.workplace == "oak_hill_college" else 1800
    return Job(
        id=agent.id,
        workplace=p.workplace,
        employer=f"business:{p.workplace}",
        kind=kind,
        hourly_cents=wage if kind in ("employment", "freelance") else 0,
        shift_start=start,
        shift_end=end,
        allowance_cents=allowance,
    )


def initial_economy(agents: list[Agent]):
    """Authored scenario contracts, independent of private real survey finances."""
    count = len(agents)
    households = Counter(a.persona.home for a in agents)
    accounts = {
        "town:treasury": count * 10000,
        "town:benefits": count * 25000,
        "town:housing": 0,
        "supplier": 0,
    }
    changes, food_total = [], count * 6
    for index, agent in enumerate(sorted(agents, key=lambda a: a.id)):
        number = int(hashlib.sha256(agent.id.encode()).hexdigest()[:8], 16)
        cash, meals = 3500 + number % 12500, 1 + number % 3
        accounts[agent.id] = cash
        food_total += meals
        job = contract(agent)
        accounts[job.employer] = accounts.get(job.employer, 200000) + 50000
        members = sorted(a.id for a in agents if a.persona.home == agent.persona.home)
        base, remainder = divmod(3600, households[agent.persona.home])
        rent = base + (members.index(agent.id) < remainder)
        lease = Lease(id=agent.id, home=agent.persona.home, daily_cents=rent)
        changes.extend(
            [
                change("inventories", agent.id, {"id": agent.id, "meals": meals}),
                change("jobs", job.id, job),
                change("leases", lease.id, lease),
            ]
        )
        remember(
            agent,
            0,
            f"My housing agreement charges ${rent / 100:.2f} each evening. "
            f"My {job.kind} agreement pays ${job.hourly_cents / 100:.2f} per hour for "
            f"eligible work, at most {job.max_daily_minutes // 60} hours daily. "
            f"My daily pension/support allowance is ${job.allowance_cents / 100:.2f}.",
            "initial_contract",
            0.85,
            "seed",
        )
        changes.append(change("agents", agent.id, agent))
    for location, factor, price in (
        ("the_willows_market_and_pharmacy", 1, 600),
        ("hobbs_cafe", 2, 800),
        ("the_rose_and_crown_pub", 4, 1000),
    ):
        stock = max(1, count // factor)
        account = f"business:{location}"
        accounts.setdefault(account, 200000)
        shop = Shop(
            id=location, account=account, price_cents=price, stock=stock, daily_target=stock
        )
        food_total += stock
        changes.append(change("shops", shop.id, shop))
    changes.extend(
        change("accounts", key, {"id": key, "cents": cents})
        for key, cents in sorted(accounts.items())
    )
    changes.extend(
        [
            change("objects", "wholesale_meals", {"id": "wholesale_meals", "units": count * 6}),
            change(
                "metadata",
                "economy",
                {
                    "initial_cents": sum(accounts.values()),
                    "initial_meals": food_total,
                    "rates": "fictional authored scenario",
                    "rent": "daily prorated household total $36, shared equally",
                    "last_restock_day": -1,
                },
            ),
        ]
    )
    return changes


class Economy:
    def __init__(self, world: WorldState, config: Config):
        self.world, self.config = world, config

    def job(self, actor: Agent) -> Job:
        return Job.model_validate(self.world.get("jobs", actor.id))

    def work_check(self, actor: Agent, minute: int, duration: int):
        job = self.job(actor)
        hour = minute % 1440
        if not job.shift_start <= hour < hour + duration <= job.shift_end:
            raise ValueError("this work period is outside my agreed hours")
        if job.worked_minutes.get(str(minute // 1440), 0) + duration > job.max_daily_minutes:
            raise ValueError("my daily work limit would be exceeded")

    def wage_changes(self, actor: Agent, start: int, minute: int):
        self.work_check(actor, start, minute - start)
        job = self.job(actor)
        day = str(start // 1440)
        job.worked_minutes[day] = job.worked_minutes.get(day, 0) + minute - start
        earned, job.cent_minute_remainder = divmod(
            (minute - start) * job.hourly_cents + job.cent_minute_remainder, 60
        )
        batch = LedgerBatch(self.world, minute, f"wage:{actor.id}")
        due = earned + job.unpaid_cents
        paid = min(due, batch.account(job.employer).cents)
        if paid:
            batch.transfer(job.employer, actor.id, paid, "wages")
        job.unpaid_cents = due - paid
        return [*batch.changes(), change("jobs", job.id, job)], {
            "earned_cents": earned,
            "paid_cents": paid,
            "unpaid_cents": job.unpaid_cents,
        }

    def purchase_check(self, actor: Agent, request: Purchase):
        shop = Shop.model_validate(self.world.get("shops", actor.location))
        if shop.stock < request.quantity:
            raise ValueError("the shop has insufficient meal stock")
        if self.world.get("accounts", actor.id)["cents"] < request.quantity * shop.price_cents:
            raise ValueError("not enough money for that purchase")
        return shop

    def purchase_changes(self, actor: Agent, request: Purchase, minute: int):
        shop = self.purchase_check(actor, request)
        batch = LedgerBatch(self.world, minute, f"purchase:{actor.id}")
        cost = shop.price_cents * request.quantity
        batch.transfer(actor.id, shop.account, cost, "meal purchase")
        shop.stock -= request.quantity
        inventory = self.world.get("inventories", actor.id)
        inventory["meals"] += request.quantity
        return [
            *batch.changes(),
            change("shops", shop.id, shop),
            change("inventories", actor.id, inventory),
        ], {"quantity": request.quantity, "cost_cents": cost, "shop": shop.id}

    def allowances(self, minute: int):
        day, batch = minute // 1440, LedgerBatch(self.world, minute, "allowances")
        changes, paid = [], 0
        for raw in self.world.all("jobs"):
            job = Job.model_validate(raw)
            if not job.allowance_cents or job.last_allowance_day >= day:
                continue
            amount = min(job.allowance_cents, batch.account("town:benefits").cents)
            if amount:
                batch.transfer("town:benefits", job.id, amount, "pension/support")
                paid += amount
            job.last_allowance_day = day
            changes.append(change("jobs", job.id, job))
        return self.world.log.append(
            minute,
            "allowances_paid",
            data={"day": day, "cents": paid},
            changes=[*batch.changes(), *changes],
        )

    def restock(self, minute: int):
        day = minute // 1440
        meta = self.world.get("metadata", "economy")
        if meta["last_restock_day"] >= day:
            raise ValueError("restock already processed today")
        delayed = day == self.config.supply_delay_day
        stock = self.world.get("objects", "wholesale_meals")
        batch, changes, delivered = LedgerBatch(self.world, minute, "restock"), [], 0
        if not delayed:
            for raw in self.world.all("shops"):
                shop = Shop.model_validate(raw)
                quantity = min(
                    max(0, shop.daily_target - shop.stock),
                    stock["units"],
                    batch.account(shop.account).cents // shop.wholesale_cents,
                )
                if quantity:
                    batch.transfer(
                        shop.account,
                        "supplier",
                        quantity * shop.wholesale_cents,
                        "wholesale replenishment",
                    )
                    stock["units"] -= quantity
                    shop.stock += quantity
                    delivered += quantity
                    changes.append(change("shops", shop.id, shop))
        meta["last_restock_day"] = day
        return self.world.log.append(
            minute,
            "shops_restocked",
            data={
                "day": day,
                "delivery_delayed": delayed,
                "delivered_meals": delivered,
                "stock": {
                    s["id"]: s["stock"]
                    for s in [
                        *(r.value for r in changes if r.table == "shops"),
                        *(
                            s
                            for s in self.world.all("shops")
                            if s["id"] not in {c.id for c in changes}
                        ),
                    ]
                },
            },
            changes=[
                *batch.changes(),
                *changes,
                change("objects", "wholesale_meals", stock),
                change("metadata", "economy", meta),
            ],
        )

    def rent(self, minute: int):
        day, batch = minute // 1440, LedgerBatch(self.world, minute, "rent")
        changes, paid, due = [], 0, 0
        for raw in self.world.all("leases"):
            lease = Lease.model_validate(raw)
            if lease.last_charged_day >= day:
                continue
            owed = lease.daily_cents + lease.arrears_cents
            amount = min(owed, batch.account(lease.id).cents)
            if amount:
                batch.transfer(lease.id, lease.landlord, amount, "prorated rent")
            lease.arrears_cents = owed - amount
            lease.paid_cents += amount
            lease.last_charged_day = day
            paid, due = paid + amount, due + lease.daily_cents
            changes.append(change("leases", lease.id, lease))
        return self.world.log.append(
            minute,
            "rent_charged",
            data={"day": day, "new_rent_cents": due, "paid_cents": paid},
            changes=[*batch.changes(), *changes],
        )

    def context(self, actor: Agent):
        # Only this person's contract/accounts and co-located shop stock.
        shop = None
        if actor.location:
            try:
                shop = self.world.get("shops", actor.location)
            except KeyError:
                pass
        return {
            "job": self.world.get("jobs", actor.id),
            "lease": self.world.get("leases", actor.id),
            "local_shop": shop,
            "known_shops": [
                {"location": s["id"], "price_cents": s["price_cents"]}
                for s in self.world.all("shops")
                if s["id"] in actor.persona.known_locations
            ],
        }
