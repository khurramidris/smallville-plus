import json
import sqlite3
from decimal import Decimal
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse

from smallville.agents.drives import advance_drives
from smallville.world.models import TABLES, Agent


def create_app(directory: str | Path) -> FastAPI:
    directory = Path(directory).resolve()
    database = directory / "world.sqlite3"
    if not database.exists():
        raise ValueError("run directory has no world.sqlite3")
    app = FastAPI(title="Smallville+ replay", docs_url="/docs")

    def connect():
        db = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
        db.row_factory = sqlite3.Row
        return db

    @lru_cache(maxsize=8)
    def state_at(minute: int, last_seq: int):
        # Explicitly keyed by the current log head, so a running simulation's
        # new events invalidate historical snapshots at the same minute.
        state = {t: {} for t in TABLES}
        with connect() as db:
            rows = db.execute(
                "SELECT record FROM events WHERE minute<=? AND seq<=? ORDER BY seq",
                (minute, last_seq),
            )
            for row in rows:
                event = json.loads(row[0])
                for change in event["changes"]:
                    state[change["table"]][change["id"]] = change["value"]
        return state

    def snapshot(minute):
        with connect() as db:
            head = db.execute("SELECT MAX(seq), MAX(minute) FROM events").fetchone()
        minute = head[1] if minute is None else min(minute, head[1])
        return minute, state_at(minute, head[0])

    def display_agent(raw, minute):
        agent = Agent.model_validate(raw)
        advance_drives(agent, minute)
        return agent.model_dump()

    @app.get("/", response_class=HTMLResponse)
    def index():
        return (Path(__file__).parent / "index.html").read_text()

    @app.get("/api/meta")
    def metadata():
        minute, state = snapshot(None)
        return {
            "map": state["metadata"]["map"],
            "run": state["metadata"]["run"],
            "minute": minute,
            "backend": state["metadata"]["config"]["backend"],
        }

    @app.get("/api/state")
    def state(minute: int | None = Query(default=None, ge=0)):
        minute, state = snapshot(minute)
        agents = []
        for raw in state["agents"].values():
            agent = display_agent(raw, minute)
            agents.append(
                {
                    key: agent[key]
                    for key in (
                        "id",
                        "persona",
                        "location",
                        "destination",
                        "activity",
                        "busy_until",
                        "pending",
                        "needs",
                        "emotion",
                    )
                }
            )
        return {"minute": minute, "agents": agents}

    @app.get("/api/agents/{identifier}")
    def inspect_agent(identifier: str, minute: int | None = Query(default=None, ge=0)):
        minute, state = snapshot(minute)
        if identifier not in state["agents"]:
            raise HTTPException(404, "Unknown resident")
        return {
            "minute": minute,
            "agent": display_agent(state["agents"][identifier], minute),
            "messages": [
                m for m in state["messages"].values() if identifier in (m["to"], m["sender"])
            ],
            "calendar": [e for e in state["calendar"].values() if e["owner"] == identifier],
        }

    @app.get("/api/events")
    def events(after: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000)):
        with connect() as db:
            rows = db.execute(
                "SELECT record FROM events WHERE seq>? ORDER BY seq LIMIT ?", (after, limit)
            )
            return [
                {k: e[k] for k in ("seq", "minute", "kind", "actor", "data")}
                for row in rows
                if (e := json.loads(row[0]))
            ]

    @app.get("/api/cost")
    def cost(minute: int | None = Query(default=None, ge=0)):
        minute, state = snapshot(minute)
        with connect() as db:
            rows = db.execute(
                "SELECT record FROM events WHERE kind='llm_call' AND minute<=?", (minute,)
            )
            calls = [json.loads(row[0])["data"] for row in rows]
        total = sum((Decimal(c["usd"]) for c in calls), Decimal(0))
        count = len(state["agents"])
        return {
            "usd": str(total),
            "max_usd": state["metadata"]["config"]["max_usd"],
            "calls": len(calls),
            "cache_hits": sum(c["cached"] for c in calls),
            "input_tokens": sum(c["input_tokens"] for c in calls),
            "output_tokens": sum(c["output_tokens"] for c in calls),
            "usd_per_agent_day": str(total / Decimal(str(count * minute / 1440)))
            if minute
            else None,
            "accounting": "mock: $0; live: configured conservative token prices",
        }

    return app
