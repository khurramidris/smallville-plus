from typing import Annotated, Literal

from pydantic import Field

from smallville.world.models import Model

Cents = Annotated[int, Field(strict=True, ge=0)]
Amount = Annotated[int, Field(strict=True, gt=0)]


class Account(Model):
    id: str
    cents: Cents


class Transfer(Model):
    id: str
    minute: int = Field(ge=0)
    source: str
    destination: str
    cents: Amount
    purpose: str


class Job(Model):
    id: str
    workplace: str
    employer: str
    kind: Literal["employment", "freelance", "study", "none"]
    hourly_cents: Cents
    shift_start: int = Field(ge=0, lt=1440)
    shift_end: int = Field(gt=0, le=1440)
    max_daily_minutes: int = Field(default=480, ge=1, le=720)
    worked_minutes: dict[str, int] = Field(default_factory=dict)
    cent_minute_remainder: int = Field(default=0, ge=0, lt=60)
    unpaid_cents: Cents = 0
    allowance_cents: Cents = 0
    last_allowance_day: int = -1


class Lease(Model):
    id: str
    home: str
    landlord: str = "town:housing"
    daily_cents: Amount
    arrears_cents: Cents = 0
    last_charged_day: int = -1
    paid_cents: Cents = 0


class Shop(Model):
    id: str
    account: str
    product: Literal["meal"] = "meal"
    price_cents: Amount
    wholesale_cents: Amount = 300
    stock: int = Field(ge=0)
    daily_target: int = Field(ge=1)


class Purchase(Model):
    item: Literal["meal"] = "meal"
    quantity: int = Field(default=1, strict=True, ge=1, le=8)


class BankTransfer(Model):
    to: str
    cents: Amount
    memo: str = Field(default="Personal transfer", min_length=1, max_length=200)
