import asyncio
import json
import sys
from decimal import Decimal
from types import SimpleNamespace

import pytest

from smallville.config import Config, Price
from smallville.llm.gateway import (
    BudgetExceeded,
    CacheMiss,
    Completion,
    Gateway,
    LiteLLMBackend,
    ModelFailure,
)


class FakeProvider:
    def __init__(self, fail=False):
        self.calls = 0
        self.fail = fail

    async def complete(self, **kwargs):
        self.calls += 1
        await asyncio.sleep(0)
        if self.fail:
            raise RuntimeError("secret-api-key-must-not-appear")
        return Completion('{"ok":true}', 10, 5)


def paid_config(cap="0.0015"):
    return Config(
        backend="litellm", allow_paid=True, max_usd=cap, max_tokens=128,
        model_deep="provider/test", model_fast="provider/test", model_gm="provider/test",
        embed_model="provider/embed", prices={"provider/test": Price(input="0.000001", output="0.000001")},
    )


async def call(gateway, dynamic=None, seed=7, temperature=0.5):
    return await gateway.complete(model="provider/test", stable="I am Pat.",
                                  dynamic=dynamic or {"task": "test"}, seed=seed,
                                  temperature=temperature)


async def test_cache_seed_parameters_and_exact_cache_replay(tmp_path):
    backend = FakeProvider()
    config = paid_config("1")
    gateway = Gateway(tmp_path / "a", config, backend, tmp_path / "shared.sqlite3")
    assert await call(gateway) == await call(gateway)
    await call(gateway, seed=8)
    await call(gateway, temperature=0.6)
    assert backend.calls == 3
    assert gateway.summary()["cache_hits"] == 1
    assert gateway.spent == Decimal("0.000045")
    gateway.close()
    config.replay_only = True
    gateway = Gateway(tmp_path / "b", config, backend, tmp_path / "shared.sqlite3")
    assert await call(gateway) == '{"ok":true}'
    with pytest.raises(CacheMiss):
        await call(gateway, seed=99)
    assert backend.calls == 3
    assert gateway.spent == 0
    gateway.close()


async def test_hard_stop_before_call_and_concurrent_reservations(tmp_path):
    backend = FakeProvider()
    gateway = Gateway(tmp_path, paid_config("0.00124"), backend)
    results = await asyncio.gather(*[call(gateway, {"task": str(i)}) for i in range(30)],
                                   return_exceptions=True)
    assert any(isinstance(x, BudgetExceeded) for x in results)
    assert backend.calls < 30
    assert gateway.spent <= gateway.config.max_usd
    gateway.close()


async def test_timeout_is_charged_conservatively_and_redacted(tmp_path):
    backend = FakeProvider(fail=True)
    config = paid_config("0.0015")
    gateway = Gateway(tmp_path, config, backend)
    with pytest.raises(ModelFailure) as error:
        await call(gateway)
    assert "secret" not in str(error.value)
    reserved = gateway.spent
    assert reserved > 0
    gateway.close()
    gateway = Gateway(tmp_path, config, backend)
    assert gateway.spent == reserved
    with pytest.raises(BudgetExceeded):
        await call(gateway)
    assert backend.calls == 1
    assert "secret-api" not in json.dumps([dict(r) for r in gateway.ledger.execute("SELECT * FROM calls")])
    gateway.close()


async def test_litellm_is_only_live_boundary(monkeypatch):
    captured = {}

    async def acompletion(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(
            usage=SimpleNamespace(prompt_tokens=12, completion_tokens=4),
            choices=[SimpleNamespace(message=SimpleNamespace(content="{}"))],
        )

    monkeypatch.setitem(sys.modules, "litellm", SimpleNamespace(acompletion=acompletion))
    response = await LiteLLMBackend(10).complete(
        model="provider/test", prompt="I am Pat.", seed=2, temperature=0.4, max_tokens=128
    )
    assert response.input_tokens == 12
    assert captured["num_retries"] == captured["max_retries"] == 0
    assert captured["messages"][0]["content"].startswith("I am")
    assert "api_key" not in captured


def test_live_config_requires_approval_and_prices(monkeypatch):
    with pytest.raises(ValueError, match="approval"):
        Config(backend="litellm")
    monkeypatch.setenv("SIM_MODEL_FAST", "provider/custom")
    assert Config.from_env().model_fast == "mock-fast"
    with pytest.raises(ValueError):
        Config(max_usd="NaN")
