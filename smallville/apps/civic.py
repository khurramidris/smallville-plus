from __future__ import annotations

import math
from typing import Literal

from pydantic import Field

from smallville.agents.memory import remember
from smallville.economy.ledger import LedgerBatch
from smallville.economy.models import Shop
from smallville.world.models import Agent, Model, change
from smallville.world.store import WorldState


class Notice(Model):
    title: str = Field(min_length=1, max_length=160)
    body: str = Field(min_length=1, max_length=2000)


class CastVote(Model):
    proposal_id: str
    choice: Literal["yes", "no", "abstain"]


def initial_council(agents: list[Agent]):
    eligible = sorted(a.id for a in agents if a.persona.age >= 18)
    return [
        change(
            "proposals",
            "community_food",
            {
                "id": "community_food",
                "title": "Fund additional affordable meal stock",
                "body": "Spend up to $300 of town funds buying meals from the finite wholesaler "
                "for the town market. Retail prices stay unchanged. Funds and supply must exist.",
                "opens": 480,
                "closes": 3600,
                "electorate": eligible,
                "quorum": math.ceil(len(eligible) / 2),
                "budget_cents": 30000,
                "status": "pending",
                "market": "the_willows_market_and_pharmacy",
            },
        )
    ]


class NoticeBoard:
    def __init__(self, world: WorldState):
        self.world = world

    def unread(self, actor: Agent, minute: int):
        try:
            cursor = self.world.get("news_reads", actor.id)
        except KeyError:
            cursor = {"last_minute": -1, "last_seq": 0}
        return [
            n
            for n in self.world.all("news")
            if n["minute"] <= minute
            and (
                n["published_seq"] > cursor.get("last_seq", 0)
                if "published_seq" in n
                else n["minute"] > cursor["last_minute"]
            )
        ]

    def next_sequence(self):
        return self.world.db.execute("SELECT COALESCE(MAX(seq),0)+1 FROM events").fetchone()[0]

    def publish(
        self,
        minute: int,
        title: str,
        body: str,
        *,
        sources: list[int],
        proposal_id: str | None = None,
        shop_reports: dict[str, int] | None = None,
    ):
        Notice(title=title, body=body)
        if not sources:
            raise ValueError("institutional news requires event evidence")
        for seq in sources:
            row = self.world.db.execute(
                "SELECT minute,kind FROM events WHERE seq=?", (seq,)
            ).fetchone()
            if (
                not row
                or row[0] > minute
                or row[1]
                not in ("shops_restocked", "proposal_opened", "council_closed", "council_policy")
            ):
                raise ValueError("news evidence is not a public town event")
        identifier = f"news:town:{minute}:{sources[-1]}"
        notice = {
            "id": identifier,
            "author": "Town bulletin",
            "category": "news",
            "minute": minute,
            "title": title,
            "body": body,
            "sources": sources,
            "proposal_id": proposal_id,
            "shop_reports": shop_reports or {},
            "published_seq": self.next_sequence(),
        }
        return self.world.log.append(
            minute,
            "news_published",
            data={"notice": identifier},
            changes=[change("news", identifier, notice)],
        )

    def read_changes(self, actor: Agent, minute: int):
        notices = sorted(
            self.unread(actor, minute),
            key=lambda n: (n["minute"], n.get("published_seq", 0), n["id"]),
        )
        # A sequence cursor retains late posts at the same simulated minute.
        # Advance only across notices actually read, preserving finite attention.
        selected = notices[:8]
        proposals = set()
        try:
            proposals.update(self.world.get("news_reads", actor.id)["proposals"])
        except KeyError:
            pass
        observations = {}
        for row in selected:
            label = "Public resident opinion" if row["category"] == "opinion" else "Town bulletin"
            remember(actor, minute, f"{label}: {row['title']}. {row['body']}", row["id"], 0.65)
            if row["proposal_id"]:
                proposals.add(row["proposal_id"])
            for location, stock in row.get("shop_reports", {}).items():
                if location in actor.persona.known_locations:
                    key = f"{actor.id}:{location}"
                    try:
                        old = self.world.get("shop_observations", key)
                    except KeyError:
                        old = {"minute": -1}
                    latest = observations.get(key, old)
                    if latest["minute"] < row["minute"]:
                        observations[key] = {
                            "id": key,
                            "owner": actor.id,
                            "location": location,
                            "stock": stock,
                            "minute": row["minute"],
                            "source": row["id"],
                        }
        last = selected[-1]["minute"] if selected else minute
        last_seq = max(
            (n.get("published_seq", 0) for n in selected), default=self.next_sequence() - 1
        )
        return [
            change(
                "news_reads",
                actor.id,
                {
                    "id": actor.id,
                    "last_minute": last,
                    "last_seq": last_seq,
                    "proposals": sorted(proposals),
                },
            ),
            *[
                change("shop_observations", key, value)
                for key, value in sorted(observations.items())
            ],
        ], selected

    def post_changes(self, actor: Agent, request: Notice, minute: int):
        identifier = f"notice:{actor.id}:{minute}"
        notice = {
            "id": identifier,
            "author": actor.id,
            "category": "opinion",
            "minute": minute,
            "title": request.title,
            "body": request.body,
            "sources": [],
            "proposal_id": None,
            "published_seq": self.next_sequence(),
        }
        return [change("news", identifier, notice)]


class Council:
    def __init__(self, world: WorldState):
        self.world = world

    def context(self, actor: Agent, minute: int):
        try:
            known = self.world.get("news_reads", actor.id)["proposals"]
        except KeyError:
            known = []
        ballots = {
            b["proposal_id"]: b["choice"]
            for b in self.world.all("ballots")
            if b["owner"] == actor.id
        }
        # No other person's choice, and no running tally before the poll closes.
        return [
            {
                **{k: v for k, v in p.items() if k != "electorate"},
                "eligible": actor.id in p["electorate"],
                "my_vote": ballots.get(p["id"]),
            }
            for p in self.world.all("proposals")
            if p["id"] in known and p["opens"] <= minute
        ]

    def validate(self, actor: Agent, request: CastVote, minute: int):
        known = {p["id"] for p in self.context(actor, minute)}
        if request.proposal_id not in known:
            raise ValueError("I need to read the council notice before voting")
        proposal = self.world.get("proposals", request.proposal_id)
        if (
            actor.id not in proposal["electorate"]
            or proposal["status"] != "open"
            or not proposal["opens"] <= minute < proposal["closes"]
        ):
            raise ValueError("I cannot vote in this poll at this time")
        try:
            self.world.get("ballots", f"{proposal['id']}:{actor.id}")
        except KeyError:
            return
        raise ValueError("I have already cast my ballot")

    def vote_changes(self, actor: Agent, request: CastVote, minute: int):
        self.validate(actor, request, minute)
        identifier = f"{request.proposal_id}:{actor.id}"
        return [
            change(
                "ballots",
                identifier,
                {
                    "id": identifier,
                    "owner": actor.id,
                    "proposal_id": request.proposal_id,
                    "choice": request.choice,
                    "minute": minute,
                },
            )
        ]

    def open(self, minute: int, identifier="community_food"):
        proposal = self.world.get("proposals", identifier)
        if minute != proposal["opens"] or proposal["status"] != "pending":
            raise ValueError("proposal is not due to open")
        proposal["status"] = "open"
        event = self.world.log.append(
            minute,
            "proposal_opened",
            data={"proposal_id": identifier},
            changes=[change("proposals", identifier, proposal)],
        )
        return NoticeBoard(self.world).publish(
            minute,
            proposal["title"],
            proposal["body"] + " Voting closes Wednesday February 15 at 12:00. "
            "One adult resident, one secret ballot; yes/no/abstain. A majority and quorum are required.",
            sources=[event.seq],
            proposal_id=identifier,
        )

    def close(self, minute: int, identifier="community_food"):
        proposal = self.world.get("proposals", identifier)
        if minute != proposal["closes"] or proposal["status"] != "open":
            raise ValueError("proposal is not due to close")
        ballots = [b for b in self.world.all("ballots") if b["proposal_id"] == identifier]
        counts = {
            choice: sum(b["choice"] == choice for b in ballots)
            for choice in ("yes", "no", "abstain")
        }
        passed = len(ballots) >= proposal["quorum"] and counts["yes"] > counts["no"]
        proposal.update(
            status="passed" if passed else "failed",
            result=counts,
            turnout=len(ballots),
            executed=False,
        )
        event = self.world.log.append(
            minute,
            "council_closed",
            data={
                "proposal_id": identifier,
                "result": counts,
                "turnout": len(ballots),
                "quorum": proposal["quorum"],
                "passed": passed,
            },
            changes=[change("proposals", identifier, proposal)],
        )
        sources, units = [event.seq], 0
        if passed:
            batch = LedgerBatch(self.world, minute, f"policy:{identifier}")
            shop = Shop.model_validate(self.world.get("shops", proposal["market"]))
            supply = self.world.get("objects", "wholesale_meals")
            funds = min(proposal["budget_cents"], batch.account("town:treasury").cents)
            units = min(supply["units"], funds // shop.wholesale_cents)
            if units:
                batch.transfer(
                    "town:treasury",
                    "supplier",
                    units * shop.wholesale_cents,
                    "council-approved meal replenishment",
                )
                supply["units"] -= units
                shop.stock += units
                proposal["executed"] = True
            proposal["delivered_meals"] = units
            outcome = self.world.log.append(
                minute,
                "council_policy",
                data={
                    "proposal_id": identifier,
                    "delivered_meals": units,
                    "spent_cents": units * shop.wholesale_cents,
                },
                changes=[
                    *batch.changes(),
                    change("shops", shop.id, shop),
                    change("objects", "wholesale_meals", supply),
                    change("proposals", identifier, proposal),
                ],
            )
            sources.append(outcome.seq)
        return NoticeBoard(self.world).publish(
            minute,
            "Council food-stock vote concluded",
            f"Yes {counts['yes']}, no {counts['no']}, abstain {counts['abstain']}; "
            f"turnout {len(ballots)}, quorum {proposal['quorum']}. "
            f"Proposal {'passed' if passed else 'failed'}. Additional meals delivered: {units}.",
            sources=sources,
            proposal_id=identifier,
            shop_reports={proposal["market"]: self.world.get("shops", proposal["market"])["stock"]}
            if units
            else {},
        )
