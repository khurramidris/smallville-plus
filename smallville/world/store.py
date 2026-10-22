from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from smallville.engine.events import Event, EventLog
from smallville.world.models import TABLES, Agent, CalendarEntry, Location, Message


class WorldState:
    def __init__(self, directory: str | Path):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.directory / "world.sqlite3")
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("PRAGMA foreign_keys=ON")
        for table in TABLES:
            self.db.execute(
                f"CREATE TABLE IF NOT EXISTS {table}(id TEXT PRIMARY KEY, data TEXT NOT NULL)"
            )
        self.db.executescript("""
            CREATE INDEX IF NOT EXISTS agents_location ON agents(json_extract(data, '$.location'));
            CREATE INDEX IF NOT EXISTS messages_recipient ON messages(json_extract(data, '$.to'));
            CREATE INDEX IF NOT EXISTS calendar_owner ON calendar(json_extract(data, '$.owner'));
            CREATE INDEX IF NOT EXISTS goals_owner ON goals(json_extract(data, '$.owner'));
            CREATE INDEX IF NOT EXISTS knowledge_owner ON knowledge(json_extract(data, '$.owner'));
        """)
        self.db.commit()
        self.log = EventLog(self.db, self.directory / "events.jsonl")

    def get(self, table: str, identifier: str) -> dict:
        if table not in TABLES:
            raise ValueError("unknown table")
        row = self.db.execute(f"SELECT data FROM {table} WHERE id=?", (identifier,)).fetchone()
        if row is None:
            raise KeyError(identifier)
        return json.loads(row[0])

    def all(self, table: str) -> list[dict]:
        if table not in TABLES:
            raise ValueError("unknown table")
        return [json.loads(r[0]) for r in self.db.execute(f"SELECT data FROM {table} ORDER BY id")]

    def agent(self, identifier: str) -> Agent:
        return Agent.model_validate(self.get("agents", identifier))

    def agents(self) -> list[Agent]:
        return [Agent.model_validate(row) for row in self.all("agents")]

    def location(self, identifier: str) -> Location:
        return Location.model_validate(self.get("locations", identifier))

    def at(self, location: str) -> list[Agent]:
        return [
            Agent.model_validate_json(r[0])
            for r in self.db.execute(
                "SELECT data FROM agents WHERE json_extract(data, '$.location')=? ORDER BY id",
                (location,),
            )
        ]

    def messages(self, owner: str) -> list[Message]:
        return [
            Message.model_validate_json(r[0])
            for r in self.db.execute(
                "SELECT data FROM messages WHERE json_extract(data, '$.to')=? "
                "OR json_extract(data, '$.sender')=? ORDER BY json_extract(data,'$.sent_at'), id",
                (owner, owner),
            )
        ]

    def calendar(self, owner: str) -> list[CalendarEntry]:
        return [
            CalendarEntry.model_validate_json(r[0])
            for r in self.db.execute(
                "SELECT data FROM calendar WHERE json_extract(data, '$.owner')=? "
                "ORDER BY json_extract(data,'$.start'), id",
                (owner,),
            )
        ]

    def snapshot(self) -> dict:
        return {table: self.all(table) for table in TABLES}

    def close(self):
        self.db.close()


def replay(source: str | Path, destination: str | Path) -> WorldState:
    target = WorldState(destination)
    if target.log.read(limit=1):
        target.close()
        raise ValueError("replay destination must be empty")
    try:
        with Path(source).open(encoding="utf-8") as file:
            for line in file:
                if not line.endswith("\n"):
                    raise ValueError("incomplete event log")
                target.log.import_event(Event.model_validate_json(line))
    except Exception:
        target.close()
        raise
    return target
