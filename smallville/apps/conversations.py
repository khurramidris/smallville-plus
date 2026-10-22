"""Consent-based private spoken conversations transported through a shared app."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, model_validator

from smallville.agents.drives import advance_drives
from smallville.agents.knowledge import campaign_knowledge_change
from smallville.agents.memory import archive_changes, remember
from smallville.agents.relationships import (
    RelationshipAppraisal,
    appraisal_changes,
    contact_change,
    relationship_id,
    relationship_state,
)
from smallville.world.maps import MapProvider
from smallville.world.models import (
    Agent,
    Conversation,
    ConversationInvitation,
    ConversationTurn,
    Model,
    RelationshipState,
    change,
)
from smallville.world.store import WorldState


class ProposeConversation(Model):
    participants: list[str] = Field(min_length=1, max_length=3)
    topic: str = Field(min_length=3, max_length=300)
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    location: str

    @model_validator(mode="after")
    def valid_people_and_time(self):
        if len(set(self.participants)) != len(self.participants):
            raise ValueError("conversation participants must be unique")
        if not 10 <= self.end - self.start <= 60:
            raise ValueError("conversation must last 10 to 60 minutes")
        return self


class RespondConversation(Model):
    conversation_id: str
    response: Literal["accept", "refuse"]
    reason: str = Field(min_length=3, max_length=500)


class ConversationDecision(Model):
    action: Literal["speak", "leave"]
    text: str = Field(default="", max_length=2000)
    appraisals: list[RelationshipAppraisal] = Field(default_factory=list, max_length=3)

    @model_validator(mode="after")
    def valid_turn(self):
        if self.action == "speak" and not self.text.strip():
            raise ValueError("a spoken turn needs text")
        peers = [item.peer for item in self.appraisals]
        if len(peers) != len(set(peers)):
            raise ValueError("only one appraisal per person is allowed each turn")
        return self


class Conversations:
    def __init__(self, world: WorldState, town: MapProvider):
        self.world, self.town = world, town

    @staticmethod
    def invitation_id(conversation_id: str, owner: str) -> str:
        return f"invite:{conversation_id}:{owner}"

    def _conversation(self, identifier: str) -> Conversation:
        return Conversation.model_validate(self.world.get("conversations", identifier))

    def conversation(self, identifier: str) -> Conversation:
        return self._conversation(identifier)

    def _invitation(self, identifier: str, owner: str) -> ConversationInvitation:
        return ConversationInvitation.model_validate(
            self.world.get("conversation_invitations", self.invitation_id(identifier, owner))
        )

    def _overlaps_commitment(
        self, owner: str, start: int, end: int, *, exclude: str | None = None
    ) -> bool:
        for row in self.world.all("conversations"):
            if row["id"] == exclude or row["status"] not in ("proposed", "active"):
                continue
            if owner not in row["accepted"]:
                continue
            if start < row["end"] and row["start"] < end:
                return True
        return False

    def _calendar_conflict(self, owner: str, start: int, end: int) -> bool:
        return any(start < event.end and event.start < end for event in self.world.calendar(owner))

    def validate_proposal(
        self, actor: Agent, request: ProposeConversation, completion_minute: int
    ) -> None:
        if actor.id in request.participants:
            raise ValueError("I cannot invite myself")
        if actor.location is None or request.location != actor.location:
            raise ValueError("a spoken conversation must be proposed where I am")
        if request.location not in actor.persona.known_locations:
            raise ValueError("I do not know that conversation location")
        if request.start < completion_minute + 5:
            raise ValueError("conversation needs time for independent replies")
        if not self.world.location(request.location).open_throughout(request.start, request.end):
            raise ValueError("conversation location is closed")
        if self._calendar_conflict(actor.id, request.start, request.end):
            raise ValueError("my calendar conflicts with this conversation")
        if self._overlaps_commitment(actor.id, request.start, request.end):
            raise ValueError("I already accepted another conversation then")
        for identifier in request.participants:
            participant = self.world.agent(identifier)
            if identifier not in actor.contacts and participant.location != actor.location:
                raise ValueError("I cannot invite someone I cannot contact")

    def proposal_changes(
        self, actor: Agent, request: ProposeConversation, minute: int
    ) -> tuple[Conversation, list]:
        self.validate_proposal(actor, request, minute)
        identifier = f"conversation:{actor.id}:{minute}"
        conversation = Conversation(
            id=identifier,
            host=actor.id,
            topic=request.topic,
            location=request.location,
            proposed_at=minute,
            start=request.start,
            end=request.end,
            invitees=request.participants,
            accepted=[actor.id],
        )
        invitations = [
            ConversationInvitation(
                id=self.invitation_id(identifier, owner),
                owner=owner,
                conversation_id=identifier,
                sender=actor.id,
            )
            for owner in request.participants
        ]
        return conversation, [
            change("conversations", conversation.id, conversation),
            *(change("conversation_invitations", item.id, item) for item in invitations),
        ]

    def _acceptance_error(
        self, actor: Agent, conversation: Conversation, minute: int
    ) -> str | None:
        if actor.location is None:
            return "I am still travelling"
        if actor.busy_until > conversation.start:
            return "I am busy when it starts"
        if conversation.location not in actor.persona.known_locations:
            return "I do not know the proposed location"
        if (
            minute + self.town.travel_minutes(actor.location, conversation.location)
            > conversation.start
        ):
            return "I cannot reach it in time"
        if self._calendar_conflict(actor.id, conversation.start, conversation.end):
            return "my calendar conflicts"
        if self._overlaps_commitment(
            actor.id, conversation.start, conversation.end, exclude=conversation.id
        ):
            return "I already accepted another conversation then"
        return None

    def validate_response(
        self, actor: Agent, request: RespondConversation, completion_minute: int
    ) -> None:
        invitation = self._invitation(request.conversation_id, actor.id)
        conversation = self._conversation(request.conversation_id)
        if invitation.status != "pending" or conversation.status != "proposed":
            raise ValueError("that invitation is no longer pending")
        if completion_minute >= conversation.start:
            raise ValueError("that invitation has expired")
        if request.response == "accept":
            if reason := self._acceptance_error(actor, conversation, completion_minute):
                raise ValueError(reason)

    def response_changes(
        self, actor: Agent, request: RespondConversation, minute: int
    ) -> tuple[Conversation, list]:
        self.validate_response(actor, request, minute)
        invitation = self._invitation(request.conversation_id, actor.id)
        conversation = self._conversation(request.conversation_id)
        invitation.status = "accepted" if request.response == "accept" else "refused"
        invitation.reason = request.reason
        invitation.responded_at = minute
        if request.response == "accept":
            if actor.id not in conversation.accepted:
                conversation.accepted.append(actor.id)
        else:
            if actor.id not in conversation.refused:
                conversation.refused.append(actor.id)
        return conversation, [
            change("conversation_invitations", invitation.id, invitation),
            change("conversations", conversation.id, conversation),
        ]

    def pending(self, actor: Agent, minute: int) -> list[dict]:
        result = []
        for row in self.world.owned("conversation_invitations", actor.id):
            if row["status"] != "pending":
                continue
            conversation = self._conversation(row["conversation_id"])
            if conversation.status != "proposed" or minute >= conversation.start:
                continue
            reason = self._acceptance_error(actor, conversation, minute + 5)
            result.append(
                {
                    "id": conversation.id,
                    "from": conversation.host,
                    "topic": conversation.topic,
                    "location": conversation.location,
                    "start": conversation.start,
                    "end": conversation.end,
                    "can_accept": reason is None,
                    "constraint": reason,
                }
            )
        return sorted(result, key=lambda row: (row["start"], row["id"]))

    def commitments(self, owner: str, minute: int) -> list[dict]:
        return sorted(
            [
                row
                for row in self.world.all("conversations")
                if row["status"] in ("proposed", "active")
                and owner in row["accepted"]
                and row["end"] > minute
            ],
            key=lambda row: (row["start"], row["id"]),
        )

    def context(self, actor: Agent, minute: int) -> dict:
        day = minute // 1440
        hosted = [
            row
            for row in self.world.all("conversations")
            if row["host"] == actor.id and row["proposed_at"] // 1440 == day
        ]
        return {
            "pending_invitations": self.pending(actor, minute),
            "commitments": self.commitments(actor.id, minute),
            "hosted_today": len(hosted),
        }

    def next_commitment(self, owner: str, minute: int) -> dict | None:
        return next(
            (
                row
                for row in self.commitments(owner, minute)
                if row["status"] == "proposed" and row["start"] >= minute
            ),
            None,
        )

    def start(self, identifier: str, minute: int):
        conversation = self._conversation(identifier)
        if conversation.status != "proposed" or minute != conversation.start:
            raise ValueError("conversation is not due to start")
        changes, observations = [], {}
        for owner in conversation.invitees:
            invitation = self._invitation(identifier, owner)
            if invitation.status == "pending":
                invitation.status = "expired"
                invitation.reason = "No reply arrived before the start."
                invitation.responded_at = minute
                changes.append(change("conversation_invitations", invitation.id, invitation))
        ordered = [
            conversation.host,
            *(owner for owner in conversation.invitees if owner in conversation.accepted),
        ]
        active, agents = [], {}
        for owner in ordered:
            actor = self.world.agent(owner)
            if (
                actor.scene_id is None
                and actor.pending is None
                and actor.busy_until <= minute
                and actor.location == conversation.location
            ):
                advance_drives(actor, minute)
                active.append(owner)
                agents[owner] = actor
            else:
                observations[owner] = "I missed the conversation because I was unavailable."
        if len(active) < 2:
            conversation.status = "ended"
            conversation.ended_at = minute
            conversation.end_reason = "fewer than two accepted residents were available"
            changes.append(change("conversations", conversation.id, conversation))
            return self.world.log.append(
                minute,
                "conversation_cancelled",
                conversation.host,
                data={
                    "conversation_id": conversation.id,
                    "reason": conversation.end_reason,
                    "wake": ordered,
                },
                changes=changes,
                observations=observations,
            )
        conversation.status = "active"
        conversation.active_participants = active
        conversation.turn_order = active
        for owner, actor in agents.items():
            actor.scene_id = conversation.id
            actor.activity = "conversation"
            actor.busy_until = conversation.end
            changes.append(change("agents", owner, actor))
            observations[owner] = f"My private conversation about {conversation.topic} has started."
        changes.append(change("conversations", conversation.id, conversation))
        return self.world.log.append(
            minute,
            "conversation_started",
            conversation.host,
            data={
                "conversation_id": conversation.id,
                "participants": active,
                "end": conversation.end,
            },
            changes=changes,
            observations=observations,
        )

    def next_speaker(self, conversation: Conversation) -> str | None:
        if conversation.status != "active" or len(conversation.active_participants) < 2:
            return None
        for offset in range(len(conversation.turn_order)):
            index = (conversation.turn_cursor + offset) % len(conversation.turn_order)
            owner = conversation.turn_order[index]
            if owner in conversation.active_participants:
                return owner
        return None

    def witnessed_turns(self, owner: str, conversation_id: str) -> dict[str, dict]:
        return {
            row["id"]: row
            for row in self.world.all("conversation_turns")
            if row["conversation_id"] == conversation_id and owner in row["observers"]
        }

    def private_context(self, actor: Agent, conversation_id: str) -> dict:
        conversation = self._conversation(conversation_id)
        if actor.id not in conversation.active_participants:
            raise ValueError("I am not part of that active conversation")
        return {
            "conversation": conversation.model_dump(mode="json"),
            "turns": sorted(
                self.witnessed_turns(actor.id, conversation_id).values(),
                key=lambda row: (row["minute"], row["id"]),
            ),
            "relationships": {
                peer: relationship_state(self.world, actor, peer).model_dump(mode="json")
                for peer in conversation.active_participants
                if peer != actor.id
            },
        }

    def record_turn(
        self, actor_id: str, conversation_id: str, decision: ConversationDecision, minute: int
    ):
        conversation = self._conversation(conversation_id)
        expected = self.next_speaker(conversation)
        if expected != actor_id:
            raise ValueError("it is not this participant's turn")
        actor = self.world.agent(actor_id)
        if actor.scene_id != conversation.id or minute >= conversation.end:
            raise ValueError("conversation turn is outside the active scene")
        witnessed = self.witnessed_turns(actor.id, conversation.id)
        advance_drives(actor, minute)
        observers = list(conversation.active_participants)
        turn = ConversationTurn(
            id=f"turn:{conversation.id}:{conversation.turn_count}",
            conversation_id=conversation.id,
            minute=minute,
            speaker=actor.id,
            action=decision.action,
            text=decision.text,
            observers=observers,
        )
        agents = {owner: self.world.agent(owner) for owner in observers}
        agents[actor.id] = actor
        changes = [change("conversation_turns", turn.id, turn)]
        relationship_changes = {}
        history_changes = []

        def add_contact(owner: str, peer: str):
            owner_actor = agents[owner]
            key = relationship_id(owner, peer)
            base = (
                RelationshipState.model_validate(relationship_changes[key].value)
                if key in relationship_changes
                else None
            )
            relationship_changes[key] = contact_change(
                self.world, owner_actor, peer, minute, turn.id, state=base
            )

        if decision.action == "speak":
            for listener in observers:
                if listener == actor.id:
                    continue
                add_contact(actor.id, listener)
                add_contact(listener, actor.id)
        for appraisal in decision.appraisals:
            key = relationship_id(actor.id, appraisal.peer)
            base = (
                RelationshipState.model_validate(relationship_changes[key].value)
                if key in relationship_changes
                else None
            )
            appraised = appraisal_changes(
                self.world,
                actor,
                conversation.id,
                minute,
                appraisal,
                witnessed,
                state=base,
            )
            relationship_changes[key] = appraised[0]
            history_changes.extend(appraised[1:])

        observations, memory_changes = {}, []
        for owner in observers:
            person = agents[owner]
            evicted = []
            if decision.action == "speak":
                text = (
                    f"I said in a private conversation: {decision.text}"
                    if owner == actor.id
                    else f"{actor.persona.name} said in our private conversation: {decision.text}"
                )
                observations[owner] = text
                memory = remember(person, minute, text, turn.id, 0.72, evicted=evicted)
                if owner != actor.id:
                    evidence = campaign_knowledge_change(
                        owner=owner,
                        text=decision.text,
                        source_id=turn.id,
                        source_kind="testimony",
                        asserted_at=minute,
                        observed_at=minute,
                        speaker=actor.id,
                        listener=owner,
                        retained_memory_id=memory.id,
                    )
                    if evidence:
                        memory_changes.append(evidence)
            else:
                text = (
                    "I left the private conversation."
                    if owner == actor.id
                    else f"{actor.persona.name} left our private conversation."
                )
                observations[owner] = text
                remember(person, minute, text, turn.id, 0.6, evicted=evicted)
            memory_changes.extend(archive_changes(owner, evicted, minute))
            person.last_social_at = minute

        actor_index = conversation.turn_order.index(actor.id)
        conversation.turn_cursor = actor_index + 1
        conversation.turn_count += 1
        wake = []
        if decision.action == "leave":
            conversation.active_participants.remove(actor.id)
            actor.scene_id = None
            actor.busy_until = minute
            actor.activity = "wait"
            wake.append(actor.id)
        if len(conversation.active_participants) < 2:
            conversation.status = "ended"
            conversation.ended_at = minute
            conversation.end_reason = "fewer than two participants remained"
            for owner in list(conversation.active_participants):
                person = agents[owner]
                advance_drives(person, minute)
                person.scene_id = None
                person.busy_until = minute
                person.activity = "wait"
                wake.append(owner)
            conversation.active_participants = []
        changes.extend(relationship_changes.values())
        changes.extend(history_changes)
        changes.extend(memory_changes)
        changes.extend(change("agents", owner, person) for owner, person in agents.items())
        changes.append(change("conversations", conversation.id, conversation))
        return self.world.log.append(
            minute,
            "conversation_turn",
            actor.id,
            data={
                "conversation_id": conversation.id,
                "turn_id": turn.id,
                "action": decision.action,
                "appraisals_applied": len(decision.appraisals),
                "ended": conversation.status == "ended",
                "wake": list(dict.fromkeys(wake)),
            },
            changes=changes,
            observations=observations,
        )

    def end(self, identifier: str, minute: int, reason: str = "scheduled end"):
        conversation = self._conversation(identifier)
        if conversation.status not in ("proposed", "active"):
            return None
        changes, observations, wake = [], {}, []
        if conversation.status == "active":
            for owner in list(conversation.active_participants):
                actor = self.world.agent(owner)
                advance_drives(actor, minute)
                actor.scene_id = None
                actor.busy_until = minute
                actor.activity = "wait"
                changes.append(change("agents", actor.id, actor))
                observations[owner] = "The private conversation ended."
                wake.append(owner)
        conversation.status = "ended"
        conversation.active_participants = []
        conversation.ended_at = minute
        conversation.end_reason = reason
        changes.append(change("conversations", conversation.id, conversation))
        return self.world.log.append(
            minute,
            "conversation_ended",
            conversation.host,
            data={"conversation_id": conversation.id, "reason": reason, "wake": wake},
            changes=changes,
            observations=observations,
        )
