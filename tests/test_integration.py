import json
from decimal import Decimal

import httpx
import pytest

from smallville.agents.mind import Mind
from smallville.cli import main, write_report
from smallville.config import Config
from smallville.engine.simulation import Simulation
from smallville.eval.interviews import interview
from smallville.eval.metrics import evaluate
from smallville.viewer.app import create_app
from smallville.world.store import replay
from tests.test_llm import paid_config


async def test_two_days_party_evaluation_replay_and_viewer(tmp_path):
    sim = Simulation(tmp_path / "town", Config())
    try:
        result = await sim.run(2)
        assert result["status"] == "completed" and result["completed_minutes"] == 2880
        assert result["agents"] == 25 and Decimal(result["cost"]["usd"]) == 0
        agents = sim.world.agents()
        assert all(sum(a.activity_minutes.values()) == 2880 for a in agents)
        assert all(0 <= value <= 100 for a in agents for value in a.needs.model_dump().values())
        report = evaluate(sim.world)
        assert report["diffusion"]["party"]["initial"] == report["diffusion"]["sam"]["initial"] == 1
        assert report["party"]["invited_guests"] > 0
        assert 0 < report["party"]["attending_guests"] <= report["party"]["invited_guests"]
        assert abs(sum(report["daily_life"]["average_hours"].values()) - 24) < 1e-9
        assert report["anti_homogeneity"]["observed_daily_behavior_variance"]["work_hours"] > 0
        assert report["evidence_label"] == "fixture only"
        assert report["paper_comparison_allowed"] is False
        assert "paper_reference" not in report
        assert report["evaluation_manifest"]["protocol_version"] == "realism-eval-v1"
        assert report["evaluation_manifest"]["population"]["kind"] == "original_25_seed_workflow"
        assert report["cost"]["purposes"]["action"] > 0
        assert report["cognition_diagnostics"]["plans"]["accepted"] > 0
        assert (
            report["cognition_diagnostics"]["interaction_opportunities"][
                "activations_with_someone_nearby"
            ]
            > 0
        )
        write_report(tmp_path / "town", report)

        restored = replay(sim.world.log.path, tmp_path / "replayed")
        try:
            assert restored.snapshot() == sim.world.snapshot()
            assert restored.log.path.read_bytes() == sim.world.log.path.read_bytes()
        finally:
            restored.close()

        app = create_app(tmp_path / "town")
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            assert (await client.get("/")).status_code == 200
            assert (await client.get("/api/meta")).json()["backend"] == "mock"
            early = (await client.get("/api/agents/isabella_rodriguez?minute=0")).json()
            assert early["messages"] == [] and early["agent"]["activity"] == "sleep"
            final = (await client.get("/api/state?minute=2880")).json()
            assert len(final["agents"]) == 25
            assert (await client.get("/api/cost")).json()["calls"] == result["cost"]["calls"]
            assert (await client.get("/api/agents/unknown")).status_code == 404
            assert (await client.get("/api/events?limit=1001")).status_code == 422
            assert (await client.get("/api/state?minute=-1")).status_code == 422
            events = (await client.get("/api/events?limit=2")).json()
            assert [e["seq"] for e in events] == [1, 2]

        answers = await interview(sim.mind, "isabella_rodriguez", 2880)
        assert len(answers) == 6 and all(a["human_rating"] is None for a in answers)
        assert answers[-1]["category"] == "campaign_recall"
        assert answers[-1]["claim_assessment"] is None
        assert all(a["available_evidence"] for a in answers)
    finally:
        sim.close()


async def test_sparse_activation_and_budget_stop(tmp_path):
    sim = Simulation(tmp_path / "asleep", Config())
    try:
        result = await sim.run(0.1)
        assert result["cost"]["calls"] == 0
        assert all(a.activity == "sleep" for a in sim.world.agents())
    finally:
        sim.close()
    # Real adapter selected, but the budget blocks dispatch. No network and no
    # credentials are involved; a cap stop cannot satisfy a full-day acceptance.
    sim = Simulation(tmp_path / "budget", paid_config("0.000001"))
    try:
        result = await sim.run(1)
        assert result["status"] == "budget_stopped"
        assert result["completed_minutes"] < 1440 and Decimal(result["cost"]["usd"]) == 0
    finally:
        sim.close()


async def test_deterministic_mock_and_exact_cached_rerun(tmp_path):
    original = Simulation(tmp_path / "a", Config(), cache_path=tmp_path / "cache.sqlite3")
    try:
        await original.run(0.375)
        original_agents = original.world.all("agents")
        history = original.world.log.path.read_bytes()
    finally:
        original.close()
    same = Simulation(tmp_path / "b", Config())
    try:
        await same.run(0.375)
        assert same.world.log.path.read_bytes() == history
    finally:
        same.close()
    cached = Simulation(
        tmp_path / "c", Config(replay_only=True), cache_path=tmp_path / "cache.sqlite3"
    )
    try:
        result = await cached.run(0.375)
        assert result["status"] == "completed"
        assert result["cost"]["cache_hits"] == result["cost"]["calls"] > 0
        assert cached.world.all("agents") == original_agents
    finally:
        cached.close()


def test_cli_preflight_never_prints_keys(monkeypatch, capsys):
    monkeypatch.setenv("OPENAI_API_KEY", "private-test-value")
    monkeypatch.setenv("OPENROUTER_API_KEY", "private-router-value")
    assert main(["preflight"]) == 0
    output = capsys.readouterr().out
    assert "private-test-value" not in output
    assert "private-router-value" not in output
    result = json.loads(output)
    assert result["paid_calls"] == 0
    assert result["credential_presence_only"]["OPENROUTER_API_KEY"] is True


async def test_invalid_plan_and_response_fail_safely(setup_world, town):
    world, config, gateway = setup_world

    class InvalidBackend:
        async def complete(self, **kwargs):
            from smallville.llm.gateway import Completion

            return Completion('{"kind":"teleport","outcome":"I own the bank"}', 4, 5)

    gateway.backend = InvalidBackend()
    mind = Mind(world, town, gateway, config)
    agent = world.agent("john_lin")
    intent = await mind.decide(agent, 600)
    assert intent.kind == "wait" and agent.plan is not None


def test_reusing_run_directory_fails(tmp_path):
    sim = Simulation(tmp_path, Config())
    try:
        with pytest.raises(ValueError, match="already contains"):
            Simulation(tmp_path, Config())
    finally:
        sim.close()
