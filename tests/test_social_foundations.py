import pytest

from smallville.agents.drives import advance_drives
from smallville.agents.relationships import (
    RelationshipAppraisal,
    appraisal_changes,
    initial_relationship_changes,
    relationship_id,
)
from smallville.apps.conversations import (
    ConversationDecision,
    Conversations,
    ProposeConversation,
    RespondConversation,
)
from smallville.apps.phone import Messaging, SendMessage
from smallville.config import Config
from smallville.engine.simulation import Simulation
from smallville.gm.master import GameMaster
from smallville.world.models import Intent, change


def _enable_connected(world, config, minute=1):
    connected = config.model_copy(update={"realism_profile": "connected_v1"})
    world.log.append(
        minute,
        "connected_test_profile",
        changes=[change("metadata", "config", connected.model_dump(mode="json"))],
    )


def test_phone_attention_reads_bounded_priority_batch_without_body_preview(setup_world):
    world, config, _ = setup_world
    _enable_connected(world, config)
    phone = Messaging(world)
    sender_id, recipient_id = "john_lin", "mei_lin"
    for minute, body, verbosity in (
        (2, "ordinary first note", "normal"),
        (3, "urgent second note", "urgent"),
        (4, "ordinary third note", "normal"),
    ):
        sender = world.agent(sender_id)
        message, changes = phone.delivery_changes(
            sender,
            SendMessage(to=recipient_id, body=body, verbosity=verbosity),
            minute,
        )
        world.log.append(
            minute,
            "message_fixture",
            sender.id,
            changes=[*changes, change("agents", sender.id, sender)],
        )
        assert message.read_at is None

    summaries = phone.notifications(recipient_id, "summary")
    assert len(summaries) == 3
    assert all("body" not in item for item in summaries)
    recipient = world.agent(recipient_id)
    changes, read, remaining = phone.check_changes(recipient, 10, limit=2)
    assert read == ["msg:john_lin:3", "msg:john_lin:2"]
    assert remaining == 1
    world.log.append(
        10,
        "phone_checked",
        recipient.id,
        changes=[*changes, change("agents", recipient.id, recipient)],
    )
    assert len(phone.notifications(recipient_id, "summary")) == 1
    attention = world.get("phone_attention", recipient_id)
    assert attention["checks"] == 1 and attention["messages_read"] == 2


def test_relationship_appraisal_is_directed_evidenced_and_emotion_decays(setup_world):
    world, _, _ = setup_world
    actor = world.agent("john_lin")
    peer = world.agent("mei_lin")
    world.log.append(
        1,
        "relationship_seed",
        changes=[
            *initial_relationship_changes(actor),
            *initial_relationship_changes(peer),
        ],
    )
    before = world.get("relationship_states", relationship_id(actor.id, peer.id))
    reverse_before = world.get("relationship_states", relationship_id(peer.id, actor.id))
    witnessed = {
        "turn:example:0": {
            "id": "turn:example:0",
            "speaker": peer.id,
            "observers": [actor.id, peer.id],
        }
    }
    appraisal = RelationshipAppraisal(
        peer=peer.id,
        trust_delta=0.1,
        affinity_delta=0.08,
        reason="I did not disagree; her concrete offer made me feel supported.",
        evidence=["turn:example:0"],
    )
    changes = appraisal_changes(world, actor, "conversation:example", 5, appraisal, witnessed)
    world.log.append(
        5,
        "relationship_appraised",
        actor.id,
        changes=[*changes, change("agents", actor.id, actor)],
    )
    after = world.get("relationship_states", relationship_id(actor.id, peer.id))
    assert after["trust"] == pytest.approx(before["trust"] + 0.1)
    assert after["affinity"] == pytest.approx(before["affinity"] + 0.08)
    assert world.get("relationship_states", relationship_id(peer.id, actor.id)) == reverse_before
    assert len(world.all("relationship_history")) == 1
    impulse = actor.emotion.social_valence
    advance_drives(actor, 65)
    assert 0 < actor.emotion.social_valence < impulse
    with pytest.raises(ValueError, match="witnessed"):
        appraisal_changes(
            world,
            actor,
            "conversation:example",
            6,
            appraisal.model_copy(update={"evidence": ["turn:private"]}),
            witnessed,
        )


async def test_conversation_invitations_require_independent_acceptance_and_time(setup_world, town):
    world, config, gateway = setup_world
    _enable_connected(world, config)
    connected = config.model_copy(update={"realism_profile": "connected_v1"})
    gm = GameMaster(world, town, gateway, connected)
    host = world.agent("john_lin")
    busy = world.agent("jane_moreno")
    busy.location = host.location
    busy.busy_until = 200
    world.log.append(2, "busy_counterpart", changes=[change("agents", busy.id, busy)])
    invitation = {
        "participants": ["mei_lin", "eddy_lin", busy.id],
        "topic": "whether to organize a shared dinner",
        "start": 130,
        "end": 150,
        "location": host.location,
    }
    started = await gm.resolve(
        host.id,
        Intent(
            kind="conversation_invite",
            text="I want to ask them to talk.",
            duration=5,
            arguments=invitation,
        ),
        100,
    )
    assert started.kind == "action_started"
    proposed = gm.complete(host.id, 105)
    conversation_id = proposed.data["conversation_id"]

    accepted = await gm.resolve(
        "mei_lin",
        Intent(
            kind="conversation_respond",
            text="I want to accept.",
            duration=5,
            arguments={
                "conversation_id": conversation_id,
                "response": "accept",
                "reason": "I have time and want to discuss it.",
            },
        ),
        105,
    )
    assert accepted.kind == "action_started"
    gm.complete("mei_lin", 110)
    refused = await gm.resolve(
        "eddy_lin",
        Intent(
            kind="conversation_respond",
            text="I want to refuse.",
            duration=5,
            arguments={
                "conversation_id": conversation_id,
                "response": "refuse",
                "reason": "I would rather keep my own plans.",
            },
        ),
        110,
    )
    assert refused.kind == "action_started"
    gm.complete("eddy_lin", 115)
    pending_busy = gm.conversations.pending(world.agent(busy.id), 115)
    assert pending_busy[0]["can_accept"] is False
    assert "busy" in pending_busy[0]["constraint"]

    stranded_host = await gm.resolve(
        host.id,
        Intent(
            kind="move",
            target="johnson_park",
            text="I want to leave even though I could not get back in time.",
        ),
        115,
    )
    assert stranded_host.kind == "action_rejected"
    assert "too little time" in stranded_host.data["reason"]

    overlap = await gm.resolve(
        "mei_lin",
        Intent(kind="wait", text="I want to ignore my commitment.", duration=30),
        115,
    )
    assert overlap.kind == "action_rejected"
    assert "overlap" in overlap.data["reason"]
    scene = gm.conversations.start(conversation_id, 130)
    assert scene.kind == "conversation_started"
    assert scene.data["participants"] == [host.id, "mei_lin"]
    assert (
        world.get(
            "conversation_invitations",
            gm.conversations.invitation_id(conversation_id, busy.id),
        )["status"]
        == "expired"
    )
    ended = gm.conversations.end(conversation_id, 150)
    assert ended.kind == "conversation_ended"


def test_three_person_private_turns_false_testimony_appraisal_and_departure(setup_world, town):
    world, config, _ = setup_world
    _enable_connected(world, config)
    conversations = Conversations(world, town)
    host = world.agent("john_lin")
    bystander = world.agent("jane_moreno")
    bystander.location = host.location
    world.log.append(2, "bystander_arrived", changes=[change("agents", bystander.id, bystander)])
    request = ProposeConversation(
        participants=["mei_lin", "eddy_lin"],
        topic="what we heard about the mayoral race",
        start=120,
        end=150,
        location=host.location,
    )
    conversation, changes = conversations.proposal_changes(host, request, 100)
    world.log.append(100, "conversation_proposed", host.id, changes=changes)
    for minute, owner in ((105, "mei_lin"), (110, "eddy_lin")):
        actor = world.agent(owner)
        current, updates = conversations.response_changes(
            actor,
            RespondConversation(
                conversation_id=conversation.id,
                response="accept",
                reason="I am willing to hear what the others say.",
            ),
            minute,
        )
        world.log.append(minute, "conversation_accepted", owner, changes=updates)
        assert owner in current.accepted
    scene = conversations.start(conversation.id, 120)
    assert scene.data["participants"] == [host.id, "mei_lin", "eddy_lin"]
    assert bystander.id not in scene.observations

    first = conversations.record_turn(
        host.id,
        conversation.id,
        ConversationDecision(
            action="speak",
            text="Sam Moore is not running for mayor; that is only a rumor.",
        ),
        120,
    )
    assert set(first.observations) == {host.id, "mei_lin", "eddy_lin"}
    assert bystander.id not in first.observations
    turn_id = first.data["turn_id"]
    second = conversations.record_turn(
        "mei_lin",
        conversation.id,
        ConversationDecision(
            action="speak",
            text="I am not convinced, but thank you for explaining what you heard.",
            appraisals=[
                RelationshipAppraisal(
                    peer=host.id,
                    trust_delta=0.06,
                    affinity_delta=0.03,
                    reason="John clearly identified the statement as an unverified rumor.",
                    evidence=[turn_id],
                )
            ],
        ),
        125,
    )
    assert second.data["ended"] is False
    conversations.record_turn(
        "eddy_lin",
        conversation.id,
        ConversationDecision(action="speak", text="I will wait for direct evidence."),
        130,
    )
    conversations.record_turn(
        host.id,
        conversation.id,
        ConversationDecision(action="speak", text="That seems cautious and fair."),
        135,
    )
    departed = conversations.record_turn(
        "mei_lin",
        conversation.id,
        ConversationDecision(action="leave", text="I need to return to my own plans."),
        140,
    )
    assert departed.data["ended"] is False
    assert world.agent("mei_lin").scene_id is None
    assert set(world.get("conversations", conversation.id)["active_participants"]) == {
        host.id,
        "eddy_lin",
    }
    assert not any(memory.source == turn_id for memory in world.agent(bystander.id).memories)
    source_owners = {row["owner"] for row in world.all("knowledge") if row["source_id"] == turn_id}
    assert source_owners == {"mei_lin", "eddy_lin"}
    transitions = world.all("relationship_history")
    assert len(transitions) == 1 and transitions[0]["owner"] == "mei_lin"
    assert transitions[0]["peer"] == host.id
    ended = conversations.end(conversation.id, 150)
    assert set(ended.data["wake"]) == {host.id, "eddy_lin"}
    assert all(world.agent(owner).scene_id is None for owner in (host.id, "eddy_lin"))


async def test_engine_runs_private_turns_and_releases_participants(tmp_path):
    sim = Simulation(tmp_path / "conversation_engine", Config())
    try:
        sim.scheduler.queue.clear()
        sim.scheduler.conditions.clear()
        owners = ("john_lin", "mei_lin", "jane_moreno")
        agents = {owner: sim.world.agent(owner) for owner in owners}
        for actor in agents.values():
            actor.location = "johnson_park"
            actor.destination = None
            actor.pending = None
            actor.busy_until = 0
            actor.activity = "wait"
        sim.world.log.append(
            0,
            "conversation_engine_fixture",
            changes=[change("agents", owner, actor) for owner, actor in agents.items()],
        )
        conversation, updates = sim.gm.conversations.proposal_changes(
            agents["john_lin"],
            ProposeConversation(
                participants=["mei_lin"],
                topic="whether to share responsibility for a neighborhood meal",
                start=10,
                end=20,
                location="johnson_park",
            ),
            0,
        )
        sim.world.log.append(0, "conversation_proposed", "john_lin", changes=updates)
        _, updates = sim.gm.conversations.response_changes(
            agents["mei_lin"],
            RespondConversation(
                conversation_id=conversation.id,
                response="accept",
                reason="I have time and want to decide for myself.",
            ),
            1,
        )
        sim.world.log.append(1, "conversation_accepted", "mei_lin", changes=updates)
        sim.scheduler.schedule(
            10,
            "conversation_start",
            data={"conversation_id": conversation.id},
            priority=5,
        )

        result = await sim.run(20 / 1440)
        assert result["status"] == "completed"
        events = sim.world.log.read(limit=1000)
        turns = [event for event in events if event.kind == "conversation_turn"]
        assert len(turns) == 2
        assert all(set(event.observations) == {"john_lin", "mei_lin"} for event in turns)
        assert all("jane_moreno" not in event.observations for event in turns)
        assert sim.world.get("conversations", conversation.id)["status"] == "ended"
        assert all(sim.world.agent(owner).scene_id is None for owner in ("john_lin", "mei_lin"))
    finally:
        sim.close()
