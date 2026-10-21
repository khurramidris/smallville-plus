from __future__ import annotations

import json
import os
from decimal import Decimal
from typing import Literal

from pydantic import Field, model_validator

from smallville.world.models import Model


class Price(Model):
    """USD per token. Set conservative ceilings covering all billable tokens."""

    input: Decimal = Field(ge=0, allow_inf_nan=False)
    output: Decimal = Field(ge=0, allow_inf_nan=False)


class Config(Model):
    backend: Literal["mock", "litellm"] = "mock"
    seed: int = 42
    max_usd: Decimal = Field(default=Decimal("0"), ge=0, allow_inf_nan=False)
    model_deep: str = "mock-deep"
    model_fast: str = "mock-fast"
    model_gm: str = "mock-gm"
    embed_model: str = "mock-lexical"
    model_overrides: dict[str, str] = Field(default_factory=dict)
    prices: dict[str, Price] = Field(default_factory=dict)
    max_tokens: int = Field(default=1200, ge=128, le=8192)
    timeout_seconds: float = Field(default=45, gt=0, le=300)
    reasoning_effort: Literal["none", "minimal", "low", "medium", "high", "xhigh", "max"] | None = (
        None
    )
    allow_paid: bool = False
    replay_only: bool = False

    @model_validator(mode="after")
    def live_ready(self):
        if self.backend == "litellm":
            if not self.allow_paid:
                raise ValueError("paid calls require explicit approval and --allow-paid")
            models = {
                self.model_deep,
                self.model_fast,
                self.model_gm,
                *self.model_overrides.values(),
            }
            if any(m.startswith("mock") or not m for m in models) or self.embed_model.startswith(
                "mock"
            ):
                raise ValueError(
                    "configure SIM_MODEL_DEEP, SIM_MODEL_FAST, SIM_MODEL_GM, SIM_EMBED_MODEL"
                )
            if models - self.prices.keys():
                raise ValueError(
                    "SIM_MODEL_PRICES must give conservative per-token prices for all models"
                )
            for model in models:
                price = self.prices[model]
                if price.input == price.output == 0 and not (
                    model.startswith("openrouter/") and model.endswith(":free")
                ):
                    raise ValueError("zero prices require an explicit OpenRouter :free model")
            if self.max_usd == 0 and any(
                self.prices[model].input or self.prices[model].output for model in models
            ):
                raise ValueError("set a positive SIM_MAX_USD for priced models")
        return self

    @classmethod
    def from_env(cls, backend="mock", seed=42, allow_paid=False, replay_only=False):
        if backend == "mock":
            return cls(seed=seed, max_usd=os.getenv("SIM_MAX_USD", "0"), replay_only=replay_only)
        return cls(
            backend=backend,
            seed=seed,
            allow_paid=allow_paid,
            replay_only=replay_only,
            max_usd=os.getenv("SIM_MAX_USD", "0"),
            model_deep=os.getenv("SIM_MODEL_DEEP", ""),
            model_fast=os.getenv("SIM_MODEL_FAST", ""),
            model_gm=os.getenv("SIM_MODEL_GM", ""),
            embed_model=os.getenv("SIM_EMBED_MODEL", ""),
            model_overrides=json.loads(os.getenv("SIM_MODEL_OVERRIDES", "{}")),
            prices=json.loads(os.getenv("SIM_MODEL_PRICES", "{}")),
            max_tokens=int(os.getenv("SIM_MAX_TOKENS", "1200")),
            timeout_seconds=float(os.getenv("SIM_TIMEOUT_SECONDS", "45")),
            reasoning_effort=os.getenv("SIM_REASONING_EFFORT") or None,
        )

    def model_for(self, identifier: str, tier: str) -> str:
        return self.model_overrides.get(
            identifier, self.model_deep if tier == "deep" else self.model_fast
        )
