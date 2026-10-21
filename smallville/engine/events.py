from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from smallville.world.models import TABLES, Change


def canonical(value: Any) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )


class Event(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    seq: int = Field(ge=1)
    minute: int = Field(ge=0)
    kind: str
    actor: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    observations: dict[str, str] = Field(default_factory=dict)
    changes: list[Change] = Field(default_factory=list)
    previous_hash: str
    hash: str

    def verify(self) -> None:
        body = self.model_dump(mode="json", exclude={"hash"})
        if hashlib.sha256(canonical(body).encode()).hexdigest() != self.hash:
            raise ValueError(f"event integrity failure at sequence {self.seq}")


class EventLog:
    """SQLite is authoritative; JSONL is a recoverable, hash-chained mirror.

    A single process owns the writer. Projection updates and their event commit
    together. Export recovery repairs an interrupted trailing write, never a
    divergent committed prefix. This is replay storage, not a secure audit vault.
    """

    def __init__(self, db: sqlite3.Connection, path: Path):
        self.db, self.path = db, path
        db.executescript("""
            CREATE TABLE IF NOT EXISTS events(
                seq INTEGER PRIMARY KEY, minute INTEGER NOT NULL,
                kind TEXT NOT NULL, actor TEXT, hash TEXT NOT NULL, record TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS events_time ON events(minute, seq);
            CREATE INDEX IF NOT EXISTS events_actor ON events(actor, seq);
            CREATE TRIGGER IF NOT EXISTS immutable_events_update BEFORE UPDATE ON events
            BEGIN SELECT RAISE(ABORT, 'events are append-only'); END;
            CREATE TRIGGER IF NOT EXISTS immutable_events_delete BEFORE DELETE ON events
            BEGIN SELECT RAISE(ABORT, 'events are append-only'); END;
        """)
        self.recover_export()

    def recover_export(self) -> None:
        records = [r[0] for r in self.db.execute("SELECT record FROM events ORDER BY seq")]
        self.path.parent.mkdir(parents=True, exist_ok=True)
        raw = self.path.read_bytes() if self.path.exists() else b""
        lines = raw.splitlines(keepends=True)
        complete = []
        for i, line in enumerate(lines):
            if not line.endswith(b"\n"):
                if i != len(lines) - 1:
                    raise ValueError("invalid JSONL framing")
                break
            complete.append(line.decode().rstrip("\n"))
        if complete != records[: len(complete)] or len(complete) > len(records):
            raise ValueError("JSONL diverges from authoritative event history")
        if len(complete) != len(records) or (raw and not raw.endswith(b"\n")):
            temporary = self.path.with_suffix(".repair")
            temporary.write_text("".join(r + "\n" for r in records))
            temporary.replace(self.path)
        elif not self.path.exists():
            self.path.touch()

    def append(
        self,
        minute: int,
        kind: str,
        actor: str | None = None,
        data: dict | None = None,
        changes: list[Change] | None = None,
        observations: dict[str, str] | None = None,
    ) -> Event:
        last = self.db.execute(
            "SELECT seq, minute, hash FROM events ORDER BY seq DESC LIMIT 1"
        ).fetchone()
        if last and minute < last[1]:
            raise ValueError("event time cannot move backwards")
        body = dict(
            seq=last[0] + 1 if last else 1,
            minute=minute,
            kind=kind,
            actor=actor,
            data=data or {},
            observations=observations or {},
            changes=[c.model_dump(mode="json") for c in changes or []],
            previous_hash=last[2] if last else "0" * 64,
        )
        event = Event(**body, hash=hashlib.sha256(canonical(body).encode()).hexdigest())
        self.import_event(event)
        return event

    def import_event(self, event: Event) -> None:
        event.verify()
        last = self.db.execute(
            "SELECT seq, minute, hash FROM events ORDER BY seq DESC LIMIT 1"
        ).fetchone()
        if event.seq != (last[0] + 1 if last else 1):
            raise ValueError("non-contiguous event sequence")
        if event.previous_hash != (last[2] if last else "0" * 64):
            raise ValueError("broken event hash chain")
        if last and event.minute < last[1]:
            raise ValueError("event time cannot move backwards")
        record = canonical(event.model_dump(mode="json"))
        with self.db:
            self.db.execute(
                "INSERT INTO events VALUES (?, ?, ?, ?, ?, ?)",
                (event.seq, event.minute, event.kind, event.actor, event.hash, record),
            )
            for update in event.changes:
                if update.table not in TABLES:
                    raise ValueError("unknown projection")
                self.db.execute(
                    f"INSERT INTO {update.table}(id, data) VALUES (?, ?) "
                    "ON CONFLICT(id) DO UPDATE SET data=excluded.data",
                    (update.id, canonical(update.value)),
                )
        with self.path.open("a", encoding="utf-8") as file:
            file.write(record + "\n")
            file.flush()
            os.fsync(file.fileno())

    def read(self, after: int = 0, until: int | None = None, limit: int = 1000) -> list[Event]:
        rows = self.db.execute(
            "SELECT record FROM events WHERE seq > ? AND minute <= ? ORDER BY seq LIMIT ?",
            (after, until if until is not None else 2**62, limit),
        )
        return [Event.model_validate_json(row[0]) for row in rows]
