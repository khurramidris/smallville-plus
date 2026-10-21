from smallville.economy.models import Account, Transfer
from smallville.world.models import change
from smallville.world.store import WorldState


class LedgerBatch:
    """Prepare atomic postings; the caller commits them with their outcome event.

    Repeated debits in a batch see previous postings. There is no mint/overdraft
    operation, and no side effect escapes a failed batch.
    """

    def __init__(self, world: WorldState, minute: int, reference: str):
        self.world, self.minute, self.reference = world, minute, reference
        self.accounts: dict[str, Account] = {}
        self.transfers: list[Transfer] = []

    def account(self, identifier: str) -> Account:
        if identifier not in self.accounts:
            self.accounts[identifier] = Account.model_validate(
                self.world.get("accounts", identifier)
            )
        return self.accounts[identifier]

    def transfer(self, source: str, destination: str, cents: int, purpose: str) -> Transfer:
        if type(cents) is not int or cents <= 0 or source == destination:
            raise ValueError("invalid bank transfer")
        debit, credit = self.account(source), self.account(destination)
        if debit.cents < cents:
            raise ValueError("not enough money")
        record = Transfer(
            id=f"tx:{self.reference}:{self.minute}:{len(self.transfers)}",
            minute=self.minute,
            source=source,
            destination=destination,
            cents=cents,
            purpose=purpose,
        )
        debit.cents -= cents
        credit.cents += cents
        self.transfers.append(record)
        return record

    def changes(self):
        return [change("accounts", key, value) for key, value in sorted(self.accounts.items())] + [
            change("transfers", row.id, row) for row in self.transfers
        ]
