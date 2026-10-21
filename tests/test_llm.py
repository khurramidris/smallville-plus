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
        backend="litellm",
        allow_paid=True,
        max_usd=cap,
        max_tokens=128,
        model_deep="provider/test",
        model_fast="provider/test",
        model_gm="provider/test",
        embed_model="provider/embed",
        prices={"provider/test": Price(input="0.000001", output="0.000001")},
    )


async def call(gateway, dynamic=None, seed=7, temperature=0.5):
    return await gateway.complete(
        model="provider/test",
        stable="I am Pat.",
        dynamic=dynamic or {"task": "test"},
        seed=seed,
        temperature=temperature,
    )


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
    results = await asyncio.gather(
        *[call(gateway, {"task": str(i)}) for i in range(30)], return_exceptions=True
    )
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
    assert "secret-api" not in json.dumps(
        [dict(r) for r in gateway.ledger.execute("SELECT * FROM calls")]
    )
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


async def test_reopened_run_cannot_raise_original_budget(tmp_path):
    backend = FakeProvider()
    gateway = Gateway(tmp_path, paid_config("0.000001"), backend)
    gateway.close()
    gateway = Gateway(tmp_path, paid_config("100"), backend)
    try:
        with pytest.raises(BudgetExceeded):
            await call(gateway)
        assert backend.calls == 0
        assert gateway.summary()["max_usd"] == "0.000001"
    finally:
        gateway.close()


def test_only_one_gateway_can_write_a_run(tmp_path):
    gateway = Gateway(tmp_path, Config(), FakeProvider())
    try:
        with pytest.raises(ValueError, match="already has a model gateway"):
            Gateway(tmp_path, Config(), FakeProvider())
    finally:
        gateway.close()


def free_config():
    model = "openrouter/minimax/minimax-m3.1-flash:free"
    return Config(
        backend="litellm",
        allow_paid=True,
        max_usd="0",
        model_deep=model,
        model_fast=model,
        model_gm=model,
        embed_model="local/lexical",
        prices={model: Price(input="0", output="0")},
    )


async def test_free_route_runs_and_replays_under_zero_cap(tmp_path):
    config = free_config()
    backend = FakeProvider()
    gateway = Gateway(tmp_path, config, backend)
    try:
        request = dict(
            model=config.model_fast, stable="I am Pat.", dynamic={"task": "test"}, seed=7
        )
        assert await gateway.complete(**request) == '{"ok":true}'
        assert await gateway.complete(**request) == '{"ok":true}'
        assert backend.calls == 1
        assert gateway.spent == 0
        assert gateway.summary()["cache_hits"] == 1
        assert gateway.summary()["max_usd"] == "0"
    finally:
        gateway.close()


def test_zero_prices_cannot_disguise_paid_models():
    config = free_config().model_dump()
    model = config["model_fast"].removesuffix(":free")
    config.update(model_deep=model, model_fast=model, model_gm=model)
    config["prices"] = {model: {"input": "0", "output": "0"}}
    with pytest.raises(ValueError, match="explicit OpenRouter :free"):
        Config(**config)
    config["prices"][model]["output"] = "0.000001"
    with pytest.raises(ValueError, match="positive SIM_MAX_USD"):
        Config(**config)
    with pytest.raises(ValueError):
        Price(input="-1", output="0")


async def test_free_adapter_prevents_paid_fallbacks(monkeypatch):
    captured = {}

    async def acompletion(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(
            usage=SimpleNamespace(prompt_tokens=12, completion_tokens=4),
            choices=[SimpleNamespace(message=SimpleNamespace(content="{}"))],
        )

    monkeypatch.setitem(sys.modules, "litellm", SimpleNamespace(acompletion=acompletion))
    await LiteLLMBackend(10, "low").complete(
        model=free_config().model_fast,
        prompt="I am Pat.",
        seed=2,
        temperature=0.4,
        max_tokens=128,
    )
    assert captured["extra_body"]["provider"] == {
        "allow_fallbacks": False,
        "max_price": {"prompt": 0, "completion": 0},
    }
    assert captured["num_retries"] == captured["max_retries"] == 0
    assert captured["reasoning_effort"] == "low"


async def test_provider_status_survives_without_secret_error_body(tmp_path, monkeypatch):
    class ProviderError(Exception):
        status_code = 429

    async def acompletion(**kwargs):
        raise ProviderError("secret-api-key-must-not-appear")

    monkeypatch.setitem(sys.modules, "litellm", SimpleNamespace(acompletion=acompletion))
    gateway = Gateway(tmp_path, free_config(), LiteLLMBackend(10))
    try:
        with pytest.raises(ModelFailure) as error:
            await gateway.complete(
                model=free_config().model_fast,
                stable="I am Pat.",
                dynamic={"task": "test"},
                seed=7,
            )
        assert error.value.status_code == 429
        assert "HTTP 429" in str(error.value)
        assert "secret" not in str(error.value)
        assert gateway.summary()["uncertain_calls"] == 1
        assert gateway.spent == 0
        assert "secret-api" not in json.dumps(
            [dict(r) for r in gateway.ledger.execute("SELECT * FROM calls")]
        )
    finally:
        gateway.close()


async def test_reasoning_effort_changes_cache_identity(tmp_path):
    config = paid_config("1")
    backend = FakeProvider()
    gateway = Gateway(tmp_path, config, backend)
    try:
        await call(gateway)
        config.reasoning_effort = "low"
        await call(gateway)
        await call(gateway)
        config.reasoning_effort = "high"
        await call(gateway)
        assert backend.calls == 3
        assert gateway.summary()["cache_hits"] == 1
    finally:
        gateway.close()


def test_live_timeout_and_reasoning_environment(monkeypatch):
    config = free_config()
    for name in ("DEEP", "FAST", "GM"):
        monkeypatch.setenv("SIM_MODEL_" + name, config.model_fast)
    monkeypatch.setenv("SIM_EMBED_MODEL", "local/lexical")
    monkeypatch.setenv(
        "SIM_MODEL_PRICES", json.dumps({config.model_fast: {"input": 0, "output": 0}})
    )
    monkeypatch.setenv("SIM_MAX_USD", "0")
    monkeypatch.setenv("SIM_TIMEOUT_SECONDS", "180")
    monkeypatch.setenv("SIM_REASONING_EFFORT", "low")
    live = Config.from_env("litellm", allow_paid=True)
    assert live.reasoning_effort == "low" and live.timeout_seconds == 180
    assert Config.from_env().reasoning_effort is None
    monkeypatch.setenv("SIM_TIMEOUT_SECONDS", "301")
    with pytest.raises(ValueError):
        Config.from_env("litellm", allow_paid=True)
