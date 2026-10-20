from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass
class SimClock:
    minute: int = 0
    epoch: datetime = datetime(2023, 2, 13, tzinfo=timezone.utc)

    def advance(self, minute: int) -> None:
        if minute < self.minute:
            raise ValueError("clock cannot move backwards")
        self.minute = minute

    @property
    def now(self) -> datetime:
        return self.epoch + timedelta(minutes=self.minute)
