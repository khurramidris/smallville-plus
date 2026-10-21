import asyncio
from decimal import Decimal

import httpx
import pytest
from pydantic import ValidationError

from smallville.agents.mind import Mind
from smallville.apps.bank import Bank
from smallville.apps.civic import CastVote, Council, Notice, NoticeBoard
from smallville.apps.phone import Calendar, CreateEvent
from smallville.cli import main
from smallville.config import Config
from smallville.economy.ledger import LedgerBatch
from smallville.economy.models import BankTransfer, Purchase
from smallville.economy.system import Economy, contract
from smallville.engine.simulation import Simulation, bootstrap
from smallville.eval.metrics import evaluate
from smallville.gm.master import GameMaster
from smallville.llm.gateway import Gateway
from smallville.llm.mock import MockLLM
from smallville.personas.seeds import load_agents
from smallville.viewer.app import create_app
from smallville.world.models import Intent, change
from smallville.world.store import WorldState, replay


@pytest.fixture
def economic_world(tmp_path, town):
    world, config = WorldState(tmp_path / "world"), Config(phase=3)
    bootstrap(world, town, config)
    actors = world.agents()
    for actor in actors:
        actor.pending, actor.busy_until, actor.activity = None, 0, "wait"
    world.log.append(0, "test_ready", changes=[change("agents", a.id, a) for a in actors])
    gateway = Gateway(tmp_path / "gateway", config, MockLLM())
    yield world, config, GameMaster(world, town, gateway, config), gateway
    gateway.close()
    world.close()


def total_cash(world):
    return sum(a["cents"] for a in world.all("accounts"))


def test_contract_distinguishes_professor_students_and_unpaid_household_work(town):
    people = {a.id: a for a in load_agents(town)}
    assert contract(people["mei_lin"]).hourly_cents == 2200
    assert contract(people["mei_lin"]).kind == "employment"
    assert contract(people["ayesha_khan"]).kind == "study"
    assert contract(people["jane_moreno"]).hourly_cents == 0
    assert contract(people["jane_moreno"]).kind == "none"


def test_invalid_scenario_is_rejected_before_creating_a_run(tmp_path, capsys):
    output = tmp_path / "invalid"
    assert main(["run", "--phase", "3", "--supply-delay-day", "-1", "--out", str(output)]) == 2
    assert not output.exists()
    assert "supply_delay_day" in capsys.readouterr().err


@pytest.mark.parametrize(
    "status,kind,limit",
    [
        ("In school", "study", 480),
        ("Working part time", "employment", 240),
        ("Working full time", "employment", 480),
        ("Keeping house", "none", 480),
        ("Retired", "none", 480),
        ("Unemployed, laid off, looking for work", "none", 480),
        ("Other", "none", 480),
    ],
)
def test_source_work_status_controls_the_authored_contract(town, status, kind, limit):
    agent = load_agents(town)[0]
    agent.persona.facts["work_status"] = status
    job = contract(agent)
    assert job.kind == kind and job.max_daily_minutes == limit


def test_ledger_atomicity_conservation_and_no_overdraft(economic_world):
    world, _, _, _ = economic_world
    before = total_cash(world)
    cash = world.get("accounts", "john_lin")["cents"]
    batch = LedgerBatch(world, 0, "test")
    for invalid in (-1, 0, 2.5, True):
        with pytest.raises(ValueError):
            batch.transfer("john_lin", "mei_lin", invalid, "invalid")
    batch.transfer("john_lin", "mei_lin", cash, "test")
    with pytest.raises(ValueError, match="money"):
        batch.transfer("john_lin", "mei_lin", 1, "invalid")
    assert world.get("accounts", "john_lin")["cents"] == cash
    world.log.append(0, "bank_test", changes=batch.changes())
    assert world.get("accounts", "john_lin")["cents"] == 0
    assert total_cash(world) == before
    assert len(world.all("transfers")) == 1


async def test_wages_require_work_time_and_keep_fractional_cents(economic_world):
    world, _, gm, gateway = economic_world
    actor = world.agent("john_lin")
    actor.location = actor.persona.workplace
    job = world.get("jobs", actor.id)
    job["hourly_cents"] = 1801
    world.log.append(
        0,
        "test_contract",
        changes=[change("agents", actor.id, actor), change("jobs", actor.id, job)],
    )
    before, employer = (
        world.get("accounts", actor.id)["cents"],
        world.get("accounts", job["employer"])["cents"],
    )
    denied = await gm.resolve(actor.id, Intent(kind="work", text="Work now", duration=1), 480)
    assert denied.kind == "action_rejected"
    assert gateway.summary()["calls"] == 0
    for minute in (540, 541):
        assert (
            await gm.resolve(
                actor.id, Intent(kind="work", text="Work a minute", duration=1), minute
            )
        ).kind == "action_started"
        assert world.get("accounts", actor.id)["cents"] == before + (minute - 540) * 30
        gm.complete(actor.id, minute + 1)
    assert world.get("accounts", actor.id)["cents"] == before + 60
    assert world.get("accounts", job["employer"])["cents"] == employer - 60
    assert world.get("jobs", actor.id)["cent_minute_remainder"] == 2


async def test_scarce_shop_stock_is_rechecked_at_completion(economic_world):
    world, _, gm, _ = economic_world
    shop = world.get("shops", "the_willows_market_and_pharmacy")
    shop["stock"] = 1
    changes = [change("shops", shop["id"], shop)]
    for identifier in ("john_lin", "mei_lin"):
        actor = world.agent(identifier)
        actor.location = shop["id"]
        changes.append(change("agents", actor.id, actor))
    world.log.append(0, "test_stock", changes=changes)
    cash, meals = (
        total_cash(world),
        {i: world.get("inventories", i)["meals"] for i in ("john_lin", "mei_lin")},
    )
    request = Intent(kind="buy", text="Buy a meal", arguments={"item": "meal", "quantity": 1})
    for identifier in meals:
        assert (await gm.resolve(identifier, request, 540)).kind == "action_started"
    assert world.get("shops", shop["id"])["stock"] == 1
    assert gm.complete("john_lin", 550).data["succeeded"]
    assert not gm.complete("mei_lin", 550).data["succeeded"]
    assert world.get("shops", shop["id"])["stock"] == 0
    assert world.get("inventories", "john_lin")["meals"] == meals["john_lin"] + 1
    assert world.get("inventories", "mei_lin")["meals"] == meals["mei_lin"]
    assert total_cash(world) == cash
    with pytest.raises(ValidationError):
        Purchase(quantity=-1)


def test_bank_authority_and_private_statements(economic_world):
    world, _, _, _ = economic_world
    actor = world.agent("john_lin")
    bank = Bank(world)
    with pytest.raises(ValidationError):
        BankTransfer.model_validate({"to": "mei_lin", "cents": 10, "owner": "sam_moore"})
    with pytest.raises(ValueError):
        bank.validate(actor, BankTransfer(to="town:treasury", cents=10))
    changes = bank.transfer_changes(actor, BankTransfer(to="mei_lin", cents=10, memo="wages"), 0)
    world.log.append(0, "bank_test", changes=changes)
    assert len(bank.statement(actor)["transactions"]) == 1
    assert bank.statement(actor)["transactions"][0]["purpose"] == "personal transfer"
    assert not bank.statement(world.agent("sam_moore"))["transactions"]


def test_daily_rent_arrears_and_allowances_are_idempotent(economic_world):
    world, config, _, _ = economic_world
    economy = Economy(world, config)
    before = total_cash(world)
    economy.allowances(360)
    snapshot = world.all("accounts")
    economy.allowances(360)
    assert world.all("accounts") == snapshot
    # Move funds, rather than manufacturing a negative balance or destroying cash.
    actor = world.agent("john_lin")
    cash = world.get("accounts", actor.id)["cents"]
    batch = LedgerBatch(world, 360, "test_shortfall")
    batch.transfer(actor.id, "town:housing", cash - 1, "test fixture")
    world.log.append(360, "test_shortfall", changes=batch.changes())
    economy.rent(1260)
    lease = world.get("leases", actor.id)
    assert lease["arrears_cents"] == lease["daily_cents"] - 1
    assert world.get("accounts", actor.id)["cents"] == 0
    snapshot = world.all("accounts")
    economy.rent(1260)
    assert snapshot == world.all("accounts")
    assert total_cash(world) == before


def test_restock_has_finite_goods_and_funding(economic_world):
    world, config, _, _ = economic_world
    shop = world.get("shops", "hobbs_cafe")
    shop["stock"] = 0
    world.log.append(
        0,
        "test_supply",
        changes=[
            change("shops", shop["id"], shop),
            change("objects", "wholesale_meals", {"id": "wholesale_meals", "units": 2}),
        ],
    )
    total = total_cash(world)
    result = Economy(world, config).restock(360)
    assert result.data["delivered_meals"] == 2
    assert world.get("objects", "wholesale_meals")["units"] == 0
    assert total_cash(world) == total
    delayed = Economy(world, config.model_copy(update={"supply_delay_day": 1})).restock(1800)
    assert delayed.data["delivery_delayed"] and delayed.data["delivered_meals"] == 0


def test_council_secret_ballots_deadlines_quorum_and_funded_policy(economic_world):
    world, _, _, _ = economic_world
    council, board = Council(world), NoticeBoard(world)
    council.open(480)
    request = CastVote(proposal_id="community_food", choice="yes")
    with pytest.raises(ValueError, match="read"):
        council.validate(world.agent("john_lin"), request, 485)
    for actor in world.agents()[:13]:
        changes, _ = board.read_changes(actor, 485)
        world.log.append(485, "test_read", changes=[*changes, change("agents", actor.id, actor)])
        world.log.append(485, "test_vote", changes=council.vote_changes(actor, request, 485))
        with pytest.raises(ValueError, match="already"):
            council.validate(actor, request, 485)
    outsider = world.agents()[-1]
    assert council.context(outsider, 485) == []
    total = total_cash(world)
    supply = world.get("objects", "wholesale_meals")["units"]
    council.close(3600)
    proposal = world.get("proposals", "community_food")
    assert proposal["status"] == "passed" and proposal["executed"]
    assert proposal["delivered_meals"] == min(100, supply)
    assert total_cash(world) == total
    with pytest.raises(ValueError):
        council.close(3600)
    with pytest.raises(ValueError):
        council.validate(world.agents()[0], request, 3600)


def test_news_evidence_and_resident_opinion_authority(economic_world):
    world, _, _, _ = economic_world
    board, actor = NoticeBoard(world), world.agent("john_lin")
    with pytest.raises(ValueError):
        board.publish(0, "Invented outcome", "Everybody voted yes", sources=[1])
    before = total_cash(world)
    updates = board.post_changes(actor, Notice(title="My claim", body="I own the town budget"), 0)
    world.log.append(0, "test_notice", changes=updates)
    assert total_cash(world) == before
    changes, rows = board.read_changes(actor, 5)
    assert rows[0]["category"] == "opinion"
    assert "Public resident opinion" in actor.memories[-1].text
    world.log.append(5, "test_read", changes=changes)
    assert not board.unread(actor, 5)


def test_news_posted_later_in_same_minute_is_not_lost(economic_world):
    world, _, _, _ = economic_world
    board = NoticeBoard(world)
    reader, author = world.agent("john_lin"), world.agent("mei_lin")
    updates, _ = board.read_changes(reader, 5)
    world.log.append(5, "test_read", changes=updates)
    updates = board.post_changes(
        author, Notice(title="New post", body="Posted after John's phone check"), 5
    )
    world.log.append(5, "test_post", changes=updates)
    assert len(board.unread(reader, 5)) == 1
    updates, selected = board.read_changes(reader, 5)
    world.log.append(5, "test_read", changes=updates)
    assert len(selected) == 1 and not board.unread(reader, 5)


def test_news_attention_limit_keeps_unread_same_minute_backlog(economic_world):
    world, _, _, _ = economic_world
    board, reader = NoticeBoard(world), world.agent("john_lin")
    for author in reversed(world.agents()[:10]):
        changes = board.post_changes(
            author, Notice(title="Update", body="My own public statement"), 5
        )
        world.log.append(5, "test_post", changes=changes)
    changes, first = board.read_changes(reader, 5)
    world.log.append(5, "test_read", changes=changes)
    assert len(first) == 8 and len(board.unread(reader, 5)) == 2


def test_council_without_quorum_cannot_spend(economic_world):
    world, _, _, _ = economic_world
    council = Council(world)
    before = total_cash(world)
    supply = world.get("objects", "wholesale_meals")
    council.open(480)
    council.close(3600)
    proposal = world.get("proposals", "community_food")
    assert proposal["status"] == "failed" and not proposal["executed"]
    assert total_cash(world) == before
    assert world.get("objects", "wholesale_meals") == supply


def test_other_residents_finances_and_ballots_do_not_enter_context(economic_world, town):
    world, config, _, gateway = economic_world
    actor = world.agent("john_lin")
    mind = Mind(world, town, gateway, config)
    before = mind.context(actor, 540, "action")
    peer = world.get("accounts", "sam_moore")
    peer["cents"] += 123456
    world.log.append(
        0,
        "test_private_state",
        changes=[
            change("accounts", peer["id"], peer),
            change(
                "ballots",
                "community_food:sam_moore",
                {
                    "id": "community_food:sam_moore",
                    "owner": "sam_moore",
                    "proposal_id": "community_food",
                    "choice": "yes",
                    "minute": 0,
                },
            ),
        ],
    )
    assert mind.context(actor, 540, "action") == before


async def test_phase3_viewer_historical_finances_and_public_town_state(economic_world):
    world, _, _, _ = economic_world
    Council(world).open(480)
    app = create_app(world.directory)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://town"
    ) as client:
        initial = (await client.get("/api/economy?minute=0")).json()
        assert initial["enabled"] and initial["news"] == []
        assert initial["proposals"][0]["status"] == "pending"
        current = (await client.get("/api/economy")).json()
        assert current["proposals"][0]["status"] == "open"
        assert "electorate" not in current["proposals"][0]
        resident = (await client.get("/api/agents/john_lin?minute=0")).json()
        assert resident["finances"]["lease"]["daily_cents"] > 0
        assert resident["finances"]["transactions"] == []
        assert (await client.get("/api/economy?minute=-1")).status_code == 422


def test_shop_observations_persist_but_do_not_reveal_remote_changes(economic_world):
    world, config, _, _ = economic_world
    economy = Economy(world, config)
    actor = world.agent("john_lin")
    actor.location = "the_willows_market_and_pharmacy"
    stock = world.get("shops", actor.location)
    world.log.append(0, "test_visit", changes=economy.perception_changes(actor, 0))
    actor.location = actor.persona.home
    stock["stock"] = 0
    world.log.append(5, "test_remote_sale", changes=[change("shops", stock["id"], stock)])
    context = economy.context(actor)
    observed = next(s for s in context["known_shops"] if s["location"] == stock["id"])
    assert observed["observed_stock"] == 25 and observed["observed_at"] == 0
    assert context["local_shop"] is None
    peer = economy.context(world.agent("sam_moore"))
    assert all(s["observed_stock"] is None for s in peer["known_shops"])


def test_only_read_bulletins_update_stock_and_preserve_newer_visits(economic_world):
    world, config, _, _ = economic_world
    economy, board = Economy(world, config), NoticeBoard(world)
    event = economy.restock(360)
    board.publish(
        360,
        "Food supply",
        "Reported morning meal stocks",
        sources=[event.seq],
        shop_reports=event.data["stock"],
    )
    actor, peer = world.agent("john_lin"), world.agent("sam_moore")
    assert all(s["observed_stock"] is None for s in economy.context(peer)["known_shops"])
    actor.location = "the_willows_market_and_pharmacy"
    shop = world.get("shops", actor.location)
    shop["stock"] = 2
    world.log.append(400, "test_sale", changes=[change("shops", shop["id"], shop)])
    world.log.append(400, "test_visit", changes=economy.perception_changes(actor, 400))
    for person in (actor, peer):
        changes, _ = board.read_changes(person, 410)
        world.log.append(410, "test_read", changes=changes)
    own = next(s for s in economy.context(actor)["known_shops"] if s["location"] == shop["id"])
    remote = next(s for s in economy.context(peer)["known_shops"] if s["location"] == shop["id"])
    assert own["observed_stock"] == 2 and own["observed_at"] == 400
    assert remote["observed_stock"] == 25 and remote["observed_at"] == 360


async def test_cancelled_simulation_records_an_incomplete_run(tmp_path):
    class CancelledBackend:
        async def complete(self, **kwargs):
            raise asyncio.CancelledError()

    sim = Simulation(tmp_path / "cancelled", Config(phase=3))
    sim.gateway.backend = CancelledBackend()
    try:
        result = await sim.run(3)
        assert result["status"] == "interrupted"
        assert 0 < result["completed_minutes"] < result["requested_minutes"] == 4320
        assert result["cost"]["uncertain_calls"] == 1
        assert sim.world.get("metadata", "run")["status"] == "interrupted"
        assert all(
            sum(a.activity_minutes.values()) == result["completed_minutes"]
            for a in sim.world.agents()
        )
    finally:
        sim.close()


async def test_received_shared_event_rejects_wrong_day(economic_world):
    world, _, gm, _ = economic_world
    host, guest = world.agent("isabella_rodriguez"), world.agent("carlos_gomez")
    host.location = guest.location = "hobbs_cafe"
    world.log.append(
        0,
        "test_scene",
        changes=[change("agents", host.id, host), change("agents", guest.id, guest)],
    )
    body = (
        "Valentine's party at Hobbs Cafe tomorrow, February 14, from 5:00 to 7:00 p.m. Please come!"
    )
    await gm.resolve(
        host.id,
        Intent(kind="message", text="Invite Carlos", arguments={"to": guest.id, "body": body}),
        660,
    )
    gm.complete(host.id, 665)
    guest = world.agent(guest.id)
    assert not gm.gatherings.visible(guest)
    updates = gm.messaging.read_changes(guest, 670)
    world.log.append(670, "test_read", changes=[*updates, change("agents", guest.id, guest)])
    assert gm.gatherings.visible(guest)[0]["id"] == "valentine_2023"
    wrong = CreateEvent(
        title="Valentine's party and poetry", start=1020, end=1140, location="hobbs_cafe"
    )
    with pytest.raises(ValueError, match="match"):
        Calendar(world).validate(guest, wrong, 675)
    correct = wrong.model_copy(update={"start": 2460, "end": 2580})
    world.log.append(
        675, "test_calendar", changes=Calendar(world).create_changes(guest, correct, 675)
    )
    await gm.resolve(guest.id, Intent(kind="attend", text="Join the host", duration=60), 2460)
    result = gm.complete(guest.id, 2520)
    assert result.data["attendance_confirmed"] and result.data["event_id"] == "valentine_2023"


@pytest.mark.parametrize("time", ["17:00–19:00", "5pm", "5:00 p.m.", "5:00 to 7:00 p.m."])
def test_full_invitation_time_formats(time):
    from smallville.agents.knowledge import party_schedule_evidence

    assert party_schedule_evidence(f"Valentine's party at Hobbs Cafe on February 14, {time}")
    assert not party_schedule_evidence("Valentine's party sometime at Hobbs Cafe")


async def test_phase3_integration_audits_and_exact_replay(tmp_path):
    sim = Simulation(tmp_path / "phase3", Config(phase=3))
    try:
        result = await sim.run(0.5)
        assert result["status"] == "completed" and Decimal(result["cost"]["usd"]) == 0
        report = evaluate(sim.world)
        assert report["diffusion"]["sam"]["initial"] == 1
        assert report["diffusion"]["party"]["initial"] == 1
        audit = report["economy"]["audit"]
        assert all(
            audit[k]
            for k in (
                "money_conserved",
                "ledger_matches_accounts",
                "food_conserved",
                "nonnegative_accounts",
                "work_limits_respected",
            )
        )
        assert report["economy"]["ballots"] > 0
        restored = replay(sim.world.log.path, tmp_path / "replay")
        try:
            assert restored.snapshot() == sim.world.snapshot()
            assert restored.log.path.read_bytes() == sim.world.log.path.read_bytes()
        finally:
            restored.close()
        cached = Simulation(
            tmp_path / "cached",
            Config(phase=3, replay_only=True),
            cache_path=tmp_path / "phase3" / "cache.sqlite3",
        )
        try:
            rerun = await cached.run(0.5)
            assert rerun["status"] == "completed"
            assert rerun["cost"]["cache_hits"] == rerun["cost"]["calls"] > 0
            expected, actual = sim.world.snapshot(), cached.world.snapshot()
            for state in (expected, actual):
                next(m for m in state["metadata"] if "replay_only" in m)["replay_only"] = False
            assert actual == expected
        finally:
            cached.close()
    finally:
        sim.close()
