import pytest

from smallville.agents.drives import advance_drives
from smallville.agents.relationships import (
    RelationshipAppraisal,
    appraisal_changes,
    initial_relationship_changes,
    relationship_id,
)
from smallville.apps.phone import Messaging, SendMessage
from smallville.world.models import change


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
