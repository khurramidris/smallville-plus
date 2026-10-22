"""Directed social state and evidence-linked appraisal changes."""

from __future__ import annotations

from pydantic import Field, model_validator

from smallville.agents.drives import clamp
from smallville.world.models import (
    Agent,
    Model,
    RelationshipState,
    RelationshipTransition,
    change,
)


class RelationshipAppraisal(Model):
    peer: str
    trust_delta: float = Field(default=0, ge=-0.15, le=0.15)
    affinity_delta: float = Field(default=0, ge=-0.15, le=0.15)
    obligation_delta: float = Field(default=0, ge=-0.15, le=0.15)
    reason: str = Field(min_length=3, max_length=500)
    evidence: list[str] = Field(min_length=1, max_length=8)

    @model_validator(mode="after")
    def meaningful_change(self):
        if not any((self.trust_delta, self.affinity_delta, self.obligation_delta)):
            raise ValueError("relationship appraisal must change at least one dimension")
        return self


def relationship_id(owner: str, peer: str) -> str:
    return f"relationship:{owner}:{peer}"


def default_state(actor: Agent, peer: str) -> RelationshipState:
    affinity = actor.relationships.get(peer, 0)
    return RelationshipState(
        id=relationship_id(actor.id, peer),
        owner=actor.id,
        peer=peer,
        trust=clamp(affinity * 0.6, -1, 1),
        affinity=affinity,
        familiarity=clamp(0.15 + abs(affinity) * 0.35, 0, 1),
    )


def initial_relationship_changes(actor: Agent):
    peers = sorted(set(actor.contacts) | set(actor.relationships))
    return [
        change("relationship_states", relationship_id(actor.id, peer), default_state(actor, peer))
        for peer in peers
    ]


def relationship_state(world, actor: Agent, peer: str) -> RelationshipState:
    try:
        return RelationshipState.model_validate(
            world.get("relationship_states", relationship_id(actor.id, peer))
        )
    except KeyError:
        return default_state(actor, peer)


def contact_change(
    world,
    actor: Agent,
    peer: str,
    minute: int,
    evidence: str,
    state: RelationshipState | None = None,
):
    """Record actual contact without guessing sentiment from its words."""

    state = (
        state.model_copy(deep=True) if state is not None else relationship_state(world, actor, peer)
    )
    state.familiarity = clamp(state.familiarity + 0.01, 0, 1)
    state.updated_at = minute
    state.evidence = [*state.evidence, evidence][-32:]
    return change("relationship_states", state.id, state)


def appraisal_changes(
    world,
    actor: Agent,
    conversation_id: str,
    minute: int,
    appraisal: RelationshipAppraisal,
    witnessed_turns: dict[str, dict],
    state: RelationshipState | None = None,
):
    if appraisal.peer == actor.id:
        raise ValueError("I cannot appraise myself as a conversation partner")
    if set(appraisal.evidence) - witnessed_turns.keys():
        raise ValueError("relationship evidence must be a turn I witnessed")
    if not any(
        witnessed_turns[identifier]["speaker"] == appraisal.peer
        for identifier in appraisal.evidence
    ):
        raise ValueError("relationship evidence must include that person's turn")
    state = (
        state.model_copy(deep=True)
        if state is not None
        else relationship_state(world, actor, appraisal.peer)
    )
    state.trust = clamp(state.trust + appraisal.trust_delta, -1, 1)
    state.affinity = clamp(state.affinity + appraisal.affinity_delta, -1, 1)
    state.obligation = clamp(state.obligation + appraisal.obligation_delta, -1, 1)
    state.updated_at = minute
    state.evidence = [*state.evidence, *appraisal.evidence][-32:]
    actor.relationships[appraisal.peer] = state.affinity
    feeling = appraisal.affinity_delta * 0.8 + appraisal.trust_delta * 0.4
    actor.emotion.social_valence = clamp(actor.emotion.social_valence + feeling, -1, 1)
    actor.emotion.social_arousal = clamp(
        actor.emotion.social_arousal
        + abs(appraisal.affinity_delta)
        + abs(appraisal.trust_delta) / 2,
        0,
        1,
    )
    evidence_key = appraisal.evidence[-1].replace(":", "_")
    identifier = (
        f"relationship_history:{conversation_id}:{actor.id}:{appraisal.peer}:{evidence_key}"
    )
    transition = RelationshipTransition(
        id=identifier,
        owner=actor.id,
        peer=appraisal.peer,
        minute=minute,
        conversation_id=conversation_id,
        trust_delta=appraisal.trust_delta,
        affinity_delta=appraisal.affinity_delta,
        obligation_delta=appraisal.obligation_delta,
        reason=appraisal.reason,
        evidence=appraisal.evidence,
    )
    return [
        change("relationship_states", state.id, state),
        change("relationship_history", transition.id, transition),
    ]
