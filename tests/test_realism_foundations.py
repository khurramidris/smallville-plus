import pytest

from smallville.agents.knowledge import campaign_claim
from smallville.agents.memory import remember, retrieve
from smallville.agents.mind import Mind
from smallville.apps.phone import Messaging, SendMessage
from smallville.config import Config
from smallville.engine.simulation import Simulation
from smallville.eval.metrics import evaluate
from smallville.llm.gateway import Gateway
from smallville.llm.mock import MockLLM
from smallville.personas.pipeline import PersonaPipeline
from smallville.personas.seeds import load_agents
from smallville.world.maps import SmallvilleMap
from smallville.world.models import change

CAMPAIGN_CASES = [
    ("I am thinking of running for local mayor.", "sam_moore", None, ("sam_moore", "considering")),
    ("I am considering a run for mayor.", "sam_moore", None, ("sam_moore", "considering")),
    ("I might run for mayor.", "sam_moore", None, ("sam_moore", "considering")),
    ("I could run for local mayor.", "sam_moore", None, ("sam_moore", "considering")),
    ("Sam may run for mayor.", "adam_smith", None, ("sam_moore", "considering")),
    ("Sam is weighing a run for mayor.", "adam_smith", None, ("sam_moore", "considering")),
    ("Sam is a potential candidate for mayor.", "adam_smith", None, ("sam_moore", "considering")),
    ("I am planning on running for local mayor.", "sam_moore", None, ("sam_moore", "declared")),
    ("I plan to run for mayor.", "sam_moore", None, ("sam_moore", "declared")),
    ("I intend to run for mayor.", "sam_moore", None, ("sam_moore", "declared")),
    ("I am running for local mayor.", "sam_moore", None, ("sam_moore", "declared")),
    ("Sam Moore is running for mayor.", "adam_smith", None, ("sam_moore", "declared")),
    ("Sam announced his campaign for mayor.", "adam_smith", None, ("sam_moore", "declared")),
    ("Sam is a candidate for mayor.", "adam_smith", None, ("sam_moore", "declared")),
    (
        "Your willingness to stand for mayor is admirable.",
        "adam_smith",
        "sam_moore",
        ("sam_moore", "declared"),
    ),
    ("I am not running for mayor.", "sam_moore", None, ("sam_moore", "denied")),
    ("I have no plans to run for mayor.", "sam_moore", None, ("sam_moore", "denied")),
    ("Sam won't run for mayor.", "adam_smith", None, ("sam_moore", "denied")),
    ("Sam dropped out of the mayoral race.", "adam_smith", None, ("sam_moore", "denied")),
    ("Sam withdrew from the mayoral race.", "adam_smith", None, ("sam_moore", "denied")),
    ("Who is running for mayor?", "adam_smith", None, None),
    ("Is Sam running for mayor?", "adam_smith", None, None),
    ("I wonder whether Sam will run for mayor.", "adam_smith", None, None),
    ("Sam should run for mayor.", "adam_smith", None, None),
    ("I encouraged Sam to run for mayor.", "adam_smith", None, None),
    ("The mayor announced a food proposal.", "adam_smith", None, None),
    ("I voted in the mayoral election.", "adam_smith", None, None),
    ("The election is next week.", "adam_smith", None, None),
    ("Maria might run for mayor.", "adam_smith", None, None),
    ("I am running late for the mayor's meeting.", "adam_smith", None, None),
    ("Sam is campaigning for better food, not for mayor.", "adam_smith", None, None),
    ("I do not think Sam is running for mayor.", "adam_smith", None, ("sam_moore", "denied")),
]


@pytest.mark.parametrize("text,speaker,listener,expected", CAMPAIGN_CASES)
def test_campaign_claim_attribution_status_and_unknowns(text, speaker, listener, expected):
    claim = campaign_claim(text, speaker=speaker, listener=listener)
    assert ((claim.subject, claim.status) if claim else None) == expected


def test_memory_keeps_identity_coalesces_routine_and_retrieves_context(town):
    agent = load_agents(town)[0]
    seeds = {memory.id for memory in agent.memories if memory.kind == "seed"}
    first_duplicate = remember(agent, 1, "I noticed the clock.", "observation", 0.1)
    second_duplicate = remember(agent, 1, "I noticed the clock.", "observation", 0.1)
    assert first_duplicate.id != second_duplicate.id
    for minute in range(1, 501):
        remember(agent, minute, f"routine detail {minute}", f"routine:{minute}", 0.01)
    for minute in range(501, 701):
        remember(agent, minute, "I finished waiting.", "gm_outcome", 0.45)
    assert len(agent.memories) == 128
    assert seeds <= {memory.id for memory in agent.memories}
    repeated = [memory for memory in agent.memories if memory.text == "I finished waiting."]
    assert len(repeated) == 1 and repeated[0].repetitions == 200
    important = remember(
        agent,
        701,
        "I promised Maria I would bring the signed application tomorrow.",
        "promise:maria",
        0.95,
    )
    assert retrieve(agent, "promise Maria signed application", 702, 1)[0].id == important.id


async def test_owner_scoped_campaign_exposure_and_metrics(setup_world):
    world, _, _ = setup_world
    sam = world.agent("sam_moore")
    adam = world.agent("adam_smith")
    if adam.id not in sam.contacts:
        sam.contacts.append(adam.id)
    request = SendMessage(
        to=adam.id,
        body="I am thinking of running for local mayor, but I have not decided yet.",
    )
    message, changes = Messaging(world).delivery_changes(sam, request, 10)
    world.log.append(10, "sent", sam.id, changes=[*changes, change("agents", sam.id, sam)])
    # Sending records Sam's own qualified self-report; it does not expose Adam.
    assert any(
        row["owner"] == sam.id
        and row["claim_status"] == "considering"
        and row["epistemic_status"] == "accepted"
        for row in world.all("knowledge")
    )
    assert not any(
        row["source_id"] == message.id for row in world.all("knowledge") if row["owner"] == adam.id
    )
    changes = Messaging(world).read_changes(adam, 12)
    world.log.append(12, "read", adam.id, changes=[*changes, change("agents", adam.id, adam)])
    exposure = [
        row
        for row in world.all("knowledge")
        if row["owner"] == adam.id and row["source_id"] == message.id
    ]
    assert len(exposure) == 1
    assert exposure[0]["epistemic_status"] == "exposed"
    assert exposure[0]["subject"] == sam.id and exposure[0]["claim_status"] == "considering"
    report = evaluate(world)
    assert {sam.id, adam.id} <= set(report["knowledge_evidence"]["campaign"]["exposed_residents"])
    assert adam.id not in report["knowledge_evidence"]["campaign"]["accepted_belief_residents"]


async def test_connected_profile_requires_and_uses_rich_population(tmp_path):
    with pytest.raises(ValueError, match="validated population"):
        Simulation(tmp_path / "missing", Config(realism_profile="connected_v1"))
    gateway = Gateway(tmp_path / "prepare", Config(), MockLLM())
    try:
        population = await PersonaPipeline(SmallvilleMap(), gateway, Config()).build(25, 14)
    finally:
        gateway.close()
    fingerprint = population.fingerprint()
    sim = Simulation(
        tmp_path / "connected",
        Config(phase=3, realism_profile="connected_v1"),
        population=population,
    )
    try:
        assert sim.world.get("metadata", "population")["history_days"] == 14
        assert all(agent.persona.life_history for agent in sim.world.agents())
        assert len(sim.world.all("goals")) >= 50
        sam = sim.world.agent("sam_moore")
        context = Mind(sim.world, sim.town, sim.gateway, sim.config).context(sam, 500, "action")
        assert context["active_goals"]
        assert "my_relationships" in context and "retrieval_query" in context
        assert (
            "plans today work family party Valentine mayor needs messages"
            not in context["retrieval_query"]
        )
        # The population artifact remains immutable after bootstrap.
        assert population.fingerprint() == fingerprint
    finally:
        sim.close()


async def test_gateway_records_request_purpose(tmp_path):
    gateway = Gateway(tmp_path, Config(), MockLLM())
    try:
        await gateway.complete(
            model="mock-fast",
            stable="I am testing purpose accounting.",
            dynamic={"task": "reflection", "memories": []},
            seed=42,
        )
        row = dict(gateway.ledger.execute("SELECT * FROM calls").fetchone())
        assert row["purpose"] == "reflection"
        assert gateway.summary()["purposes"] == {"reflection": 1}
    finally:
        gateway.close()
