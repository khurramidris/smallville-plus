import json

from smallville.economy.ledger import LedgerBatch
from smallville.economy.models import BankTransfer
from smallville.world.models import Agent
from smallville.world.store import WorldState


class Bank:
    def __init__(self, world: WorldState):
        self.world = world

    def statement(self, actor: Agent) -> dict:
        # No arbitrary owner argument: capabilities are tied to the active actor.
        rows = self.world.db.execute(
            "SELECT data FROM transfers WHERE json_extract(data,'$.source')=? "
            "OR json_extract(data,'$.destination')=? ORDER BY json_extract(data,'$.minute'), id",
            (actor.id, actor.id),
        )
        return {
            "account": self.world.get("accounts", actor.id),
            "transactions": [json.loads(r[0]) for r in rows][-8:],
        }

    def validate(self, actor: Agent, request: BankTransfer):
        if request.to == actor.id or request.to not in actor.contacts:
            raise ValueError("bank recipient must be one of my contacts")
        self.world.agent(request.to)  # Institutional accounts are not personal recipients.
        if self.world.get("accounts", actor.id)["cents"] < request.cents:
            raise ValueError("not enough money")

    def transfer_changes(self, actor: Agent, request: BankTransfer, minute: int):
        self.validate(actor, request)
        batch = LedgerBatch(self.world, minute, f"bank:{actor.id}")
        batch.transfer(actor.id, request.to, request.cents, request.memo)
        return batch.changes()
