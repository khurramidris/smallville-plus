import pytest

from smallville.agents.drives import advance_drives, conversation_effect
from smallville.agents.knowledge import campaign_evidence, party_schedule_evidence
from smallville.agents.memory import remember, retrieve
from smallville.agents.mind import Mind
from smallville.agents.perception import perceive
from smallville.apps.phone import Calendar, CreateEvent, Messaging, SendMessage
from smallville.gm.master import GameMaster, RuleViolation
from smallville.personas.seeds import load_agents
from smallville.world.models import Intent, change


def test_original_personas_heterogeneity_and_seed_privacy(town):
    agents = load_agents(town)
    assert len({a.id for a in agents}) == 25
    assert {a.persona.tier for a in agents} == {"deep", "standard"}
    assert len({a.persona.temperature for a in agents}) > 10
    party = [a.id for a in agents if any("Valentine" in m.text for m in a.memories)]
    assert party == ["isabella_rodriguez"]
    campaign = [a.id for a in agents if any(campaign_evidence(a.id, m.text) for m in a.memories)]
    assert campaign == ["sam_moore"]
    assert not campaign_evidence("john_lin", "I wonder who will be running for mayor.")
    assert not party_schedule_evidence("I can't make the Valentine's party.")


def test_drives_time_memory_limit_and_closeness(town):
    agent = load_agents(town)[0]
    agent.activity = "work"
    energy = agent.needs.energy
    advance_drives(agent, 180)
    assert agent.needs.energy < energy and agent.activity_minutes["work"] == 180
    agent.activity = "sleep"
    advance_drives(agent, 660)
    assert agent.needs.energy > energy
    for i in range(160):
        remember(agent, i + 660, f"unimportant detail {i}", str(i), 0.01)
    remember(agent, 900, "Valentine party at Hobbs Cafe", "letter", 1)
    assert len(agent.memories) == 128
    assert retrieve(agent, "Valentine party", 901, 1)[0].source == "letter"
    conversation_effect(agent, "peer", "I disagree")
    assert agent.relationships["peer"] < 0
    with pytest.raises(ValueError):
        advance_drives(agent, 0)


def test_perception_and_phone_privacy(setup_world):
    world, _, _ = setup_world
    actor = world.agent("isabella_rodriguez")
    other = world.agent("john_lin")
    phone = Messaging(world)
    with pytest.raises(ValueError):
        phone.validate(actor, SendMessage(to=other.id, body="hello"))
    view = perceive(world, actor, 0)
    assert other.id not in str(view)
    assert "memories" not in str(view) and "relationships" not in str(view)
    assert phone.inbox(actor.id) == []


async def test_gm_rejects_without_inference_and_cannot_teleport(setup_world, town):
    world, config, gateway = setup_world
    gm = GameMaster(world, town, gateway, config)
    actor = world.agent("isabella_rodriguez")
    result = await gm.resolve(
        actor.id, Intent(kind="move", target="hobbs_cafe", text="I arrive."), 0
    )
    assert result.kind == "action_rejected"
    assert gateway.summary()["calls"] == 0
    result = await gm.resolve(
        actor.id, Intent(kind="move", target="hobbs_cafe", text="I want to walk."), 500
    )
    assert result.kind == "action_started"
    moving = world.agent(actor.id)
    assert moving.location is None and moving.busy_until > 500
    blocked = await gm.resolve(actor.id, Intent(kind="work", text="I work instantly."), 501)
    assert blocked.kind == "action_rejected"
    result = gm.complete(actor.id, moving.busy_until)
    assert world.agent(actor.id).location == "hobbs_cafe"
    assert result.observations.keys() == {actor.id}


async def test_capacity_and_inventory_money_checks(setup_world, town):
    world, config, gateway = setup_world
    gm = GameMaster(world, town, gateway, config)
    actor = world.agent("isabella_rodriguez")
    with pytest.raises(RuleViolation, match="money"):
        gm.resources(actor, cost_cents=10001)
    with pytest.raises(RuleViolation, match="food"):
        gm.resources(actor, meals=13)
    result = await gm.resolve(actor.id, Intent(kind="eat", text="I want breakfast."), 0)
    assert result.kind == "action_started"
    gm.complete(actor.id, 30)
    assert world.get("inventories", actor.id)["meals"] == 11
    cafe = world.location("hobbs_cafe")
    cafe.capacity = 1
    peer = world.agent("john_lin")
    peer.location = cafe.id
    world.log.append(
        500,
        "capacity_test",
        changes=[
            change("locations", cafe.id, cafe),
            change("agents", peer.id, peer),
        ],
    )
    result = await gm.resolve(
        actor.id, Intent(kind="move", text="I want to go.", target=cafe.id), 500
    )
    assert result.kind == "action_rejected" and "space" in result.data["reason"]


async def test_messaging_delivery_read_and_calendar_ownership(setup_world, town):
    world, config, gateway = setup_world
    gm = GameMaster(world, town, gateway, config)
    actor = world.agent("john_lin")
    request = {"to": "mei_lin", "body": "I disagree with that plan."}
    await gm.resolve(
        actor.id, Intent(kind="message", text="I want to text Mei.", arguments=request), 0
    )
    assert not world.messages("mei_lin")
    gm.complete(actor.id, 5)
    peer = world.agent("mei_lin")
    assert not any("disagree with that plan" in m.text for m in peer.memories)
    changes = gm.messaging.read_changes(peer, 10)
    world.log.append(10, "read", peer.id, changes=[*changes, change("agents", peer.id, peer)])
    assert any("disagree with that plan" in m.text for m in peer.memories)
    assert len(Messaging(world).inbox("sam_moore")) == 0
    calendar = Calendar(world)
    entry = CreateEvent(title="Coffee", start=600, end=630, location="hobbs_cafe")
    changes = calendar.create_changes(peer, entry, 10)
    world.log.append(10, "calendar_test", changes=changes)
    assert len(calendar.list_events(peer.id)) == 1
    assert not calendar.list_events(actor.id)
    with pytest.raises(ValueError, match="conflict"):
        calendar.validate(peer, entry, 10)
    with pytest.raises(ValueError):
        CreateEvent.model_validate(entry.model_dump() | {"owner": "john_lin"})


async def test_mind_plan_reflection_and_ambiguous_gm(setup_world, town):
    world, config, gateway = setup_world
    agent = world.agent("isabella_rodriguez")
    mind = Mind(world, town, gateway, config)
    prefix = mind.stable_prompt(agent)
    assert prefix.startswith("My name is Isabella")
    assert "assistant" not in prefix.lower() and "simulated" not in prefix.lower()
    intent = await mind.decide(agent, 500)
    assert agent.plan and intent.kind in ("calendar", "message", "move", "work")
    await mind.reflect(agent, 1260)
    assert any(m.kind == "reflection" for m in agent.memories)
    gm = GameMaster(world, town, gateway, config)
    calls = gateway.summary()["calls"]
    result = await gm.resolve(
        agent.id, Intent(kind="attempt", text="I want to sketch the clouds."), 0
    )
    assert result.kind == "action_started" and gateway.summary()["calls"] == calls + 1
