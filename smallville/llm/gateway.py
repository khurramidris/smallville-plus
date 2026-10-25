from __future__ import annotations

import asyncio
import fcntl
import hashlib
import logging
import math
import os
import sqlite3
import time
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Callable, Protocol

from smallville.config import Config
from smallville.engine.events import canonical
from smallville.llm.prompts import has_meta_terms


class BudgetExceeded(RuntimeError):
    pass


class ModelFailure(RuntimeError):
    def __init__(self, message: str, *, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class CacheMiss(ModelFailure):
    pass


class ResidentPromptViolation(ModelFailure):
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

    def __init__(self, timeout: float, reasoning_effort: str | None = None):
        self.timeout = timeout
        self.reasoning_effort = reasoning_effort

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
        options = {}
        if self.reasoning_effort is not None:
            options["reasoning_effort"] = self.reasoning_effort
        if model.startswith("openrouter/") and model.endswith(":free"):
            # The user selected this free route, never a paid fallback. Enforce
            # zero provider pricing as well as the gateway's zero-dollar cap.
            options["extra_body"] = {
                "provider": {
                    "allow_fallbacks": False,
                    "max_price": {"prompt": 0, "completion": 0},
                }
            }
        try:
            result = await litellm.acompletion(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                seed=seed,
                max_tokens=max_tokens,
                timeout=self.timeout,
                num_retries=0,
                max_retries=0,
                stream=False,
                **options,
            )
        except Exception as exc:
            # Status codes are useful for diagnosing auth/quota/network errors.
            # Provider exception strings and response bodies may contain secrets.
            status = getattr(exc, "status_code", None)
            status = status if type(status) is int and 100 <= status <= 599 else None
            suffix = f" (HTTP {status})" if status is not None else ""
            raise ModelFailure("provider request failed" + suffix, status_code=status) from None
        usage = result.usage
        if usage is None or usage.prompt_tokens is None or usage.completion_tokens is None:
            raise ModelFailure("provider did not return billable usage")
        content = result.choices[0].message.content
        if not isinstance(content, str) or not content:
            raise ModelFailure("provider did not return text")
        return Completion(content, usage.prompt_tokens, usage.completion_tokens)


class Gateway:
    def __init__(
        self,
        directory: Path,
        config: Config,
        backend: Backend,
        cache_path: Path | None = None,
        on_call: Callable[[dict], None] | None = None,
    ):
        directory.mkdir(parents=True, exist_ok=True)
        self._lock_file = (directory / ".calls.lock").open("a")
        try:
            fcntl.flock(self._lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self._lock_file.close()
            raise ValueError("this run already has a model gateway writer") from None
        self.config, self.backend, self.on_call = config, backend, on_call
        self.lock = asyncio.Lock()
        self.slots = asyncio.Semaphore(config.decision_concurrency)
        self.request_locks = [asyncio.Lock() for _ in range(64)]
        self.ledger = sqlite3.connect(directory / "calls.sqlite3")
        self.ledger.row_factory = sqlite3.Row
        self.ledger.execute("PRAGMA journal_mode=WAL")
        self.ledger.execute("""
            CREATE TABLE IF NOT EXISTS calls(
                id INTEGER PRIMARY KEY, model TEXT NOT NULL, prompt_hash TEXT NOT NULL,
                seed INTEGER NOT NULL, purpose TEXT NOT NULL, status TEXT NOT NULL, cached INTEGER NOT NULL,
                input_tokens INTEGER NOT NULL, output_tokens INTEGER NOT NULL,
                usd TEXT NOT NULL, reservation TEXT NOT NULL)
        """)
        columns = {row[1] for row in self.ledger.execute("PRAGMA table_info(calls)")}
        if "purpose" not in columns:
            self.ledger.execute(
                "ALTER TABLE calls ADD COLUMN purpose TEXT NOT NULL DEFAULT 'legacy_unknown'"
            )
        self.ledger.execute("""
            CREATE TABLE IF NOT EXISTS call_timings(
                call_id INTEGER PRIMARY KEY, queue_ms REAL NOT NULL,
                provider_ms REAL NOT NULL, total_ms REAL NOT NULL)
        """)
        self.ledger.execute(
            "CREATE TABLE IF NOT EXISTS run_budget(id INTEGER PRIMARY KEY CHECK(id=1), cap TEXT NOT NULL)"
        )
        self.ledger.execute(
            "INSERT OR IGNORE INTO run_budget(id,cap) VALUES(1,?)", (str(config.max_usd),)
        )
        # Reopening a run (for example to interview residents) must not silently
        # raise the original spending limit through changed environment values.
        recorded_cap = Decimal(
            self.ledger.execute("SELECT cap FROM run_budget WHERE id=1").fetchone()[0]
        )
        self.max_usd = min(config.max_usd, recorded_cap)
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
            (
                Decimal(r[0])
                for r in self.ledger.execute(
                    "SELECT CASE WHEN status='reserved' THEN reservation ELSE usd END FROM calls"
                )
            ),
            Decimal(0),
        )

    def summary(self) -> dict:
        rows = list(self.ledger.execute("SELECT * FROM calls ORDER BY id"))
        return {
            "calls": len(rows),
            "cache_hits": sum(r["cached"] for r in rows),
            "input_tokens": sum(r["input_tokens"] for r in rows),
            "output_tokens": sum(r["output_tokens"] for r in rows),
            "usd": str(self.spent),
            "max_usd": str(self.max_usd),
            "uncertain_calls": sum(r["status"] in ("reserved", "uncertain") for r in rows),
            "purposes": {
                purpose: sum(r["purpose"] == purpose for r in rows)
                for purpose in sorted({r["purpose"] for r in rows})
            },
            "accounting": "conservative configured token prices; not a provider invoice",
        }

    def _insert(self, model, digest, seed, purpose, status, cached, reservation):
        with self.ledger:
            cursor = self.ledger.execute(
                "INSERT INTO calls(model,prompt_hash,seed,purpose,status,cached,input_tokens,"
                "output_tokens,usd,reservation) VALUES(?,?,?,?,?,?,0,0,'0',?)",
                (model, digest, seed, purpose, status, cached, str(reservation)),
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

    def timing_summary(self) -> dict:
        rows = list(self.ledger.execute("SELECT * FROM call_timings ORDER BY call_id"))
        provider = sorted(row[2] for row in rows if row[2] > 0)
        return {
            "timed_calls": len(rows),
            "provider_calls": len(provider),
            "provider_seconds_sum": round(sum(provider) / 1000, 3),
            "provider_ms_mean": round(sum(provider) / len(provider), 3) if provider else None,
            "provider_ms_p50": round(provider[(len(provider) - 1) // 2], 3) if provider else None,
            "provider_ms_p95": round(provider[math.ceil(len(provider) * 0.95) - 1], 3)
            if provider
            else None,
            "queue_ms_sum": round(sum(row[1] for row in rows), 3),
            "note": "Provider duration includes network and generation; concurrent durations overlap.",
        }

    async def complete(
        self,
        *,
        model: str,
        stable: str,
        dynamic: dict,
        seed: int,
        temperature: float = 0.7,
        resident: bool = False,
    ) -> str:
        prompt = stable + "\n\nCURRENT CONTEXT:\n" + canonical(dynamic)
        if resident and has_meta_terms(prompt):
            # Fail before hashing, cache reads, reservations or dispatch. Never echo
            # private prompt text into errors, and never rewrite received testimony.
            raise ResidentPromptViolation("resident prompt contains prohibited meta terminology")
        # Sampling parameters are part of the prompt hash's request envelope.
        envelope = {
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": self.config.max_tokens,
            "schema_version": 1,
        }
        if self.config.reasoning_effort is not None:
            envelope["reasoning_effort"] = self.config.reasoning_effort
        digest = hashlib.sha256(canonical(envelope).encode()).hexdigest()
        purpose = str(dynamic.get("task", "unknown"))[:80]
        started = time.perf_counter()
        # Serialize duplicate prompts, not unrelated requests. Recheck the cache
        # after waiting; a peer may have populated it while this task queued.
        request_lock = self.request_locks[int(digest[:8], 16) % len(self.request_locks)]
        async with request_lock, self.slots:
            return await self._dispatch(model, prompt, digest, seed, temperature, purpose, started)

    async def _dispatch(self, model, prompt, digest, seed, temperature, purpose, started):
        provider_started = None
        identifier = None
        async with self.lock:
            cached = self.cache.execute(
                "SELECT content FROM responses WHERE model=? AND prompt_hash=? AND seed=?",
                (model, digest, seed),
            ).fetchone()
            if cached:
                identifier = self._insert(model, digest, seed, purpose, "cached", 1, Decimal(0))
                self._finish(identifier, "cached", 0, 0, Decimal(0))
                return cached[0]
            if self.config.replay_only:
                identifier = self._insert(model, digest, seed, purpose, "cache_miss", 0, Decimal(0))
                self._finish(identifier, "cache_miss", 0, 0, Decimal(0))
                raise CacheMiss("exact replay requested but response is absent from cache")

            # UTF-8 bytes plus framing is a conservative text-token bound.
            # Only text completions are supported; no images/tools/retrieval fees.
            input_bound = len(prompt.encode("utf-8")) + 1024
            price = self.config.prices.get(model)
            reservation = (
                (
                    Decimal(input_bound) * price.input
                    + Decimal(self.config.max_tokens) * price.output
                )
                if self.config.backend == "litellm" and price
                else Decimal(0)
            )
            if self.config.backend == "litellm" and price is None:
                raise ModelFailure("missing model price: refusing unbounded paid call")
            if self.spent + reservation > self.max_usd:
                identifier = self._insert(
                    model, digest, seed, purpose, "budget_blocked", 0, Decimal(0)
                )
                self._finish(identifier, "budget_blocked", 0, 0, Decimal(0))
                raise BudgetExceeded("next call reservation exceeds SIM_MAX_USD")
            identifier = self._insert(model, digest, seed, purpose, "reserved", 0, reservation)
        try:
            try:
                provider_started = time.perf_counter()
                response = await self.backend.complete(
                    model=model,
                    prompt=prompt,
                    seed=seed,
                    temperature=temperature,
                    max_tokens=self.config.max_tokens,
                )
                if response.input_tokens < 0 or response.output_tokens < 0:
                    raise ModelFailure("invalid provider usage")
                if self.config.backend == "litellm" and (
                    response.input_tokens > input_bound
                    or response.output_tokens > self.config.max_tokens
                ):
                    raise ModelFailure("provider exceeded reserved token bound; reconcile billing")
                usd = (
                    (
                        Decimal(response.input_tokens) * price.input
                        + Decimal(response.output_tokens) * price.output
                    )
                    if self.config.backend == "litellm"
                    else Decimal(0)
                )
            except BaseException as exc:
                # An interrupted/failed request may still be billable. Keep its
                # full reservation charged, and stop the run without retries.
                self._finish(identifier, "uncertain", 0, 0, reservation)
                if isinstance(exc, (KeyboardInterrupt, SystemExit, asyncio.CancelledError)):
                    raise
                status = exc.status_code if isinstance(exc, ModelFailure) else None
                suffix = f" (HTTP {status})" if status is not None else ""
                raise ModelFailure(
                    "model request failed" + suffix + "; reservation retained; see call ledger",
                    status_code=status,
                ) from None
            self._finish(identifier, "ok", response.input_tokens, response.output_tokens, usd)
            with self.cache:
                self.cache.execute(
                    "INSERT OR IGNORE INTO responses VALUES(?,?,?,?,?,?)",
                    (
                        model,
                        digest,
                        seed,
                        response.content,
                        response.input_tokens,
                        response.output_tokens,
                    ),
                )
            return response.content
        finally:
            ended = time.perf_counter()
            if identifier is not None:
                with self.ledger:
                    self.ledger.execute(
                        "INSERT OR REPLACE INTO call_timings VALUES(?,?,?,?)",
                        (
                            identifier,
                            (provider_started - started) * 1000 if provider_started else 0,
                            (ended - provider_started) * 1000 if provider_started else 0,
                            (ended - started) * 1000,
                        ),
                    )

    def close(self):
        self.ledger.close()
        self.cache.close()
        fcntl.flock(self._lock_file, fcntl.LOCK_UN)
        self._lock_file.close()
