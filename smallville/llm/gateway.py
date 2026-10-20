from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import sqlite3
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Callable, Protocol

from smallville.config import Config
from smallville.engine.events import canonical


class BudgetExceeded(RuntimeError):
    pass


class ModelFailure(RuntimeError):
    pass


class CacheMiss(ModelFailure):
    pass


@dataclass(frozen=True)
class Completion:
    content: str
    input_tokens: int
    output_tokens: int


class Backend(Protocol):
    async def complete(
        self, *, model: str, prompt: str, seed: int, temperature: float, max_tokens: int
    ) -> Completion: ...


class LiteLLMBackend:
    """No direct provider client is permitted outside LiteLLM.

    Imports are lazy so even LiteLLM/tokenizer initialization is absent from the
    MockLLM path. Keys are read by LiteLLM from the process environment.
    """

    def __init__(self, timeout: float):
        self.timeout = timeout

    async def complete(self, *, model, prompt, seed, temperature, max_tokens):
        os.environ["LITELLM_LOCAL_MODEL_COST_MAP"] = "True"
        import litellm

        litellm.suppress_debug_info = True
        litellm.set_verbose = False
        litellm.turn_off_message_logging = True
        litellm.telemetry = False
        # Never print provider exception bodies, prompts or credentials.
        for name in ("LiteLLM", "litellm", "httpx", "httpcore", "openai"):
            logging.getLogger(name).setLevel(logging.CRITICAL)
        result = await litellm.acompletion(
            model=model, messages=[{"role": "user", "content": prompt}],
            temperature=temperature, seed=seed, max_tokens=max_tokens,
            timeout=self.timeout, num_retries=0, max_retries=0,
            stream=False,
        )
        usage = result.usage
        if usage is None or usage.prompt_tokens is None or usage.completion_tokens is None:
            raise ModelFailure("provider did not return billable usage")
        content = result.choices[0].message.content
        if not isinstance(content, str) or not content:
            raise ModelFailure("provider did not return text")
        return Completion(content, usage.prompt_tokens, usage.completion_tokens)


class Gateway:
    def __init__(
        self, directory: Path, config: Config, backend: Backend,
        cache_path: Path | None = None, on_call: Callable[[dict], None] | None = None,
    ):
        directory.mkdir(parents=True, exist_ok=True)
        self.config, self.backend, self.on_call = config, backend, on_call
        self.lock = asyncio.Lock()
        self.ledger = sqlite3.connect(directory / "calls.sqlite3")
        self.ledger.row_factory = sqlite3.Row
        self.ledger.execute("PRAGMA journal_mode=WAL")
        self.ledger.execute("""
            CREATE TABLE IF NOT EXISTS calls(
                id INTEGER PRIMARY KEY, model TEXT NOT NULL, prompt_hash TEXT NOT NULL,
                seed INTEGER NOT NULL, status TEXT NOT NULL, cached INTEGER NOT NULL,
                input_tokens INTEGER NOT NULL, output_tokens INTEGER NOT NULL,
                usd TEXT NOT NULL, reservation TEXT NOT NULL)
        """)
        self.ledger.commit()
        cache_path = cache_path or directory / "cache.sqlite3"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache = sqlite3.connect(cache_path)
        self.cache.execute("PRAGMA journal_mode=WAL")
        self.cache.execute("""
            CREATE TABLE IF NOT EXISTS responses(
                model TEXT, prompt_hash TEXT, seed INTEGER,
                content TEXT, input_tokens INTEGER, output_tokens INTEGER,
                PRIMARY KEY(model, prompt_hash, seed))
        """)
        self.cache.commit()

    @property
    def spent(self) -> Decimal:
        return sum(
            (Decimal(r[0]) for r in self.ledger.execute(
                "SELECT CASE WHEN status='reserved' THEN reservation ELSE usd END FROM calls"
            )), Decimal(0),
        )

    def summary(self) -> dict:
        rows = list(self.ledger.execute("SELECT * FROM calls ORDER BY id"))
        return {
            "calls": len(rows), "cache_hits": sum(r["cached"] for r in rows),
            "input_tokens": sum(r["input_tokens"] for r in rows),
            "output_tokens": sum(r["output_tokens"] for r in rows),
            "usd": str(self.spent), "max_usd": str(self.config.max_usd),
            "uncertain_calls": sum(r["status"] in ("reserved", "uncertain") for r in rows),
            "accounting": "conservative configured token prices; not a provider invoice",
        }

    def _insert(self, model, digest, seed, status, cached, reservation):
        with self.ledger:
            cursor = self.ledger.execute(
                "INSERT INTO calls(model,prompt_hash,seed,status,cached,input_tokens,"
                "output_tokens,usd,reservation) VALUES(?,?,?,?,?,0,0,'0',?)",
                (model, digest, seed, status, cached, str(reservation)),
            )
        return cursor.lastrowid

    def _finish(self, identifier, status, input_tokens, output_tokens, usd):
        with self.ledger:
            self.ledger.execute(
                "UPDATE calls SET status=?,input_tokens=?,output_tokens=?,usd=? WHERE id=?",
                (status, input_tokens, output_tokens, str(usd), identifier),
            )
        row = dict(self.ledger.execute("SELECT * FROM calls WHERE id=?", (identifier,)).fetchone())
        if self.on_call:
            self.on_call(row)

    async def complete(
        self, *, model: str, stable: str, dynamic: dict, seed: int,
        temperature: float = 0.7,
    ) -> str:
        prompt = stable + "\n\nCURRENT CONTEXT:\n" + canonical(dynamic)
        # Sampling parameters are part of the prompt hash's request envelope.
        digest = hashlib.sha256(canonical({
            "prompt": prompt, "temperature": temperature,
            "max_tokens": self.config.max_tokens, "schema_version": 1,
        }).encode()).hexdigest()
        async with self.lock:
            cached = self.cache.execute(
                "SELECT content FROM responses WHERE model=? AND prompt_hash=? AND seed=?",
                (model, digest, seed),
            ).fetchone()
            if cached:
                identifier = self._insert(model, digest, seed, "cached", 1, Decimal(0))
                self._finish(identifier, "cached", 0, 0, Decimal(0))
                return cached[0]
            if self.config.replay_only:
                identifier = self._insert(model, digest, seed, "cache_miss", 0, Decimal(0))
                self._finish(identifier, "cache_miss", 0, 0, Decimal(0))
                raise CacheMiss("exact replay requested but response is absent from cache")

            # UTF-8 bytes plus framing is a conservative text-token bound.
            # Only text completions are supported; no images/tools/retrieval fees.
            input_bound = len(prompt.encode("utf-8")) + 1024
            price = self.config.prices.get(model)
            reservation = (
                Decimal(input_bound) * price.input +
                Decimal(self.config.max_tokens) * price.output
            ) if self.config.backend == "litellm" and price else Decimal(0)
            if self.config.backend == "litellm" and price is None:
                raise ModelFailure("missing model price: refusing unbounded paid call")
            if self.spent + reservation > self.config.max_usd:
                identifier = self._insert(model, digest, seed, "budget_blocked", 0, Decimal(0))
                self._finish(identifier, "budget_blocked", 0, 0, Decimal(0))
                raise BudgetExceeded("next call reservation exceeds SIM_MAX_USD")
            identifier = self._insert(model, digest, seed, "reserved", 0, reservation)
            try:
                response = await self.backend.complete(
                    model=model, prompt=prompt, seed=seed,
                    temperature=temperature, max_tokens=self.config.max_tokens,
                )
                if response.input_tokens < 0 or response.output_tokens < 0:
                    raise ModelFailure("invalid provider usage")
                if self.config.backend == "litellm" and (
                    response.input_tokens > input_bound or
                    response.output_tokens > self.config.max_tokens
                ):
                    raise ModelFailure("provider exceeded reserved token bound; reconcile billing")
                usd = (
                    Decimal(response.input_tokens) * price.input +
                    Decimal(response.output_tokens) * price.output
                ) if self.config.backend == "litellm" else Decimal(0)
            except BaseException as exc:
                # An interrupted/failed request may still be billable. Keep its
                # full reservation charged, and stop the run without retries.
                self._finish(identifier, "uncertain", 0, 0, reservation)
                if isinstance(exc, (KeyboardInterrupt, SystemExit, asyncio.CancelledError)):
                    raise
                raise ModelFailure("model request failed; reservation retained; see call ledger") from None
            self._finish(identifier, "ok", response.input_tokens, response.output_tokens, usd)
            with self.cache:
                self.cache.execute(
                    "INSERT INTO responses VALUES(?,?,?,?,?,?)",
                    (model, digest, seed, response.content, response.input_tokens, response.output_tokens),
                )
            return response.content

    def close(self):
        self.ledger.close()
        self.cache.close()
