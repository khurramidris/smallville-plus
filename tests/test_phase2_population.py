import json
from collections import Counter

import httpx
import pytest

from smallville.cli import main
from smallville.config import Config
from smallville.engine.simulation import Simulation
from smallville.eval.metrics import evaluate
from smallville.llm.gateway import Completion, Gateway
from smallville.llm.mock import MockLLM
from smallville.personas.generation import source_population
from smallville.personas.histories import HistoryTemplates
from smallville.personas.pipeline import ConsistencyFailure, PersonaPipeline
from smallville.personas.population import Population
from smallville.personas.seeds import load_agents
from smallville.viewer.app import create_app
from smallville.world.maps import SmallvilleMap
from smallville.world.models import CalendarEntry, Message
from smallville.world.store import replay


@pytest.fixture(scope="module")
def population(tmp_path_factory):
    import asyncio

    directory = tmp_path_factory.mktemp("prepared-population")
    config = Config()
    gateway = Gateway(directory, config, MockLLM())
    try:
        result = asyncio.run(PersonaPipeline(SmallvilleMap(), gateway, config).build())
        result.validate_map(SmallvilleMap(extra_locations=result.locations))
        result.save(directory / "population.json")
        assert gateway.summary()["calls"] == 300
        return result
    finally:
        gateway.close()


def test_population_originals_source_facts_histories_and_capacity(population):
    assert len(population.agents) == 100 and len({a.id for a in population.agents}) == 100
    assert len(population.messages) == 4200 and len(population.calendar) == 300
    assert len(population.locations) == 75
    assert all(a.passed for a in population.consistency)
    assert all(len(a.persona.life_history.events) >= 6 for a in population.agents)
    assert all(
        e.age <= a.persona.age for a in population.agents for e in a.persona.life_history.events
    )
    by_id = {a.id: a for a in population.agents}
    for original in load_agents(SmallvilleMap()):
        assert by_id[original.id].persona.age == original.persona.age
        assert by_id[original.id].persona.home == original.persona.home
    assert all(
        m.sent_at < 0 and (m.read_at is None or m.sent_at <= m.read_at <= 0)
        for m in population.messages
    )
    assert not any(
        "valentine" in m.body.lower() or "mayor" in m.body.lower() for m in population.messages
    )
    assert all(e.start < e.end < 0 for e in population.calendar)
    assert all(
        a.persona.life_history.narrative.startswith("My name is " + a.persona.name)
        for a in population.agents
    )
    homes = Counter(a.persona.home for a in population.agents)
    town = SmallvilleMap(extra_locations=population.locations)
    assert all(count <= town.locations[identifier].capacity for identifier, count in homes.items())


def test_artifact_integrity_and_original_identity_guards(population, tmp_path):
    path = tmp_path / "population.json"
    population.save(path)
    assert Population.load(path).digest == population.digest
    data = json.loads(path.read_text())
    data["agents"][0]["persona"]["speech_style"] = "changed"
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="digest"):
        Population.load(path)
    data = population.model_dump()
    data["digest"] = ""
    data["agents"][0]["memories"] = []
    changed = Population.model_validate(data)
    with pytest.raises(ValueError, match="original seed memories"):
        changed.validate_map(SmallvilleMap(extra_locations=changed.locations))
    data = population.model_dump()
    data["digest"] = ""
    data["messages"][0]["sent_at"] = 1
    with pytest.raises(ValueError):
        Population.model_validate(data)


async def test_contradiction_regenerates_then_resurveys(tmp_path):
    class ContradictOnce(MockLLM):
        def __init__(self):
            self.changed = False

        async def complete(self, **kwargs):
            result = await super().complete(**kwargs)
            context = json.loads(kwargs["prompt"].rsplit("\n\nCURRENT CONTEXT:\n", 1)[1])
            if context["task"] == "survey" and not self.changed:
                self.changed = True
                data = json.loads(result.content)
                data["answers"]["age"] += 1
                return Completion(json.dumps(data), result.input_tokens, result.output_tokens)
            return result

    gateway = Gateway(tmp_path, Config(), ContradictOnce())
    try:
        result = await PersonaPipeline(SmallvilleMap(), gateway, Config()).build(25)
        assert len(result.consistency) == 26
        assert result.consistency[0].contradictions == ["age"]
        assert not result.consistency[0].passed and result.consistency[1].passed
        assert result.consistency[1].attempt == 2
    finally:
        gateway.close()


async def test_unresolved_consistency_prevents_publication(tmp_path):
    class AlwaysWrong(MockLLM):
        async def complete(self, **kwargs):
            context = json.loads(kwargs["prompt"].rsplit("\n\nCURRENT CONTEXT:\n", 1)[1])
            if context["task"] == "survey":
                return Completion('{"answers": {}}', 1, 1)
            return await super().complete(**kwargs)

    gateway = Gateway(tmp_path, Config(), AlwaysWrong())
    try:
        pipeline = PersonaPipeline(SmallvilleMap(), gateway, Config(), max_attempts=2)
        with pytest.raises(ConsistencyFailure, match="population not published"):
            await pipeline.build(25)
        assert len(pipeline.attempts) == 2
        assert not (tmp_path / "population.json").exists()
    finally:
        gateway.close()


def test_phone_template_and_historical_timestamp_guards():
    with pytest.raises(ValueError):
        HistoryTemplates(
            openings=["Come to the Valentine's party tomorrow!"] * 3,
            replies=["That sounds good to me."] * 3,
        )
    with pytest.raises(ValueError):
        HistoryTemplates(
            openings=["Hello {sender_name.__class__}, how are you?"] * 3,
            replies=["That sounds good to me."] * 3,
        )
    with pytest.raises(ValueError):
        Message(id="x", sender="a", to="b", body="Hello", sent_at=-10, read_at=-20)
    event = CalendarEntry(
        id="x",
        owner="a",
        title="A past appointment",
        start=-60,
        end=-30,
        location="home",
        attendees=["a"],
    )
    assert event.end == -30
    with pytest.raises(ValueError):
        source_population(SmallvilleMap(), 101, 42)


async def test_hundred_residents_bootstrap_run_replay_and_history_view(population, tmp_path):
    digest = population.fingerprint()
    sim = Simulation(tmp_path / "run", Config(), population=population)
    try:
        result = await sim.run(0.375)
        assert result["status"] == "completed" and result["agents"] == 100
        assert all(sum(a.activity_minutes.values()) == 540 for a in sim.world.agents())
        assert len(sim.world.all("messages")) >= 4200
        assert sim.world.get("metadata", "population")["history_days"] == 21
        assert population.fingerprint() == digest
        report = evaluate(sim.world)
        assert report["historical_messages"] == 4200 and report["agents"] == 100
        assert report["cost"]["usd"] == "0"
        restored = replay(sim.world.log.path, tmp_path / "replayed")
        try:
            assert restored.snapshot() == sim.world.snapshot()
        finally:
            restored.close()
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=create_app(tmp_path / "run")), base_url="http://test"
        ) as client:
            assert len((await client.get("/api/state?minute=0")).json()["agents"]) == 100
            identifier = population.agents[-1].id
            data = (await client.get(f"/api/agents/{identifier}?minute=0")).json()
            assert data["agent"]["persona"]["life_history"] and data["messages"]
            assert all(m["sent_at"] < 0 for m in data["messages"])
    finally:
        sim.close()


async def test_cached_population_build_is_exact(tmp_path):
    config = Config()
    first_gateway = Gateway(tmp_path / "a", config, MockLLM(), tmp_path / "cache.sqlite3")
    try:
        first = await PersonaPipeline(SmallvilleMap(), first_gateway, config).build(25)
    finally:
        first_gateway.close()
    config.replay_only = True
    second_gateway = Gateway(tmp_path / "b", config, MockLLM(), tmp_path / "cache.sqlite3")
    try:
        second = await PersonaPipeline(SmallvilleMap(), second_gateway, config).build(25)
        assert first.fingerprint() == second.fingerprint()
        assert second_gateway.summary()["cache_hits"] == second_gateway.summary()["calls"] == 75
    finally:
        second_gateway.close()


def test_population_cli_validation_is_offline(population, tmp_path, capsys):
    path = tmp_path / "population.json"
    population.save(path)
    assert main(["validate-population", "--population", str(path)]) == 0
    assert json.loads(capsys.readouterr().out)["residents"] == 100
