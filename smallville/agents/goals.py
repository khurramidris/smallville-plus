"""Durable, owner-scoped goals kept outside the fallible memory stream."""

from __future__ import annotations

from hashlib import sha256
from typing import Literal

from pydantic import Field, model_validator

from smallville.world.models import Agent, Goal, GoalTransition, Model, change


class GoalRequest(Model):
    goal_id: str
    action: Literal["revise", "block", "activate", "complete", "abandon"]
    reason: str = Field(min_length=3, max_length=500)
    description: str | None = Field(default=None, min_length=3, max_length=1000)
    priority: float | None = Field(default=None, ge=0, le=1)
    deadline: int | None = None
    progress: str | None = Field(default=None, max_length=500)
    evidence: list[str] = Field(default_factory=list, max_length=16)

    @model_validator(mode="after")
    def valid_revision(self):
        changes = "deadline" in self.model_fields_set or any(
            getattr(self, field) is not None for field in ("description", "priority", "progress")
        )
        if self.action == "revise" and not changes:
            raise ValueError("revision must change a goal field")
        return self


def initial_goals(agent: Agent) -> list[Goal]:
    if agent.persona.life_history:
        descriptions = agent.persona.life_history.goals
        source = "generated_life_history"
    else:
        # Original seed order is current state, daily plan request, then social
        # whispers. Use the current-state memory as an explicit initial motive.
        descriptions = [
            next(
                (memory.text for memory in agent.memories if memory.source == "original_seed"),
                "Keep my ordinary responsibilities and personal plans.",
            )
        ]
        source = "original_seed"
    goals = [
        Goal(
            id=f"goal:{agent.id}:{index}",
            owner=agent.id,
            description=description,
            priority=max(0.4, 0.9 - index * 0.15),
            source=source,
            created_at=0,
        )
        for index, description in enumerate(descriptions[:4])
    ]
    for memory in agent.memories:
        if not memory.source.startswith("historical_commitment:"):
            continue
        parts = memory.source.split(":", 2)
        deadline = int(parts[1]) if len(parts) == 3 and parts[1].isdigit() else None
        digest = sha256(memory.source.encode()).hexdigest()[:12]
        goals.append(
            Goal(
                id=f"goal:{agent.id}:commitment:{digest}",
                owner=agent.id,
                description=memory.text,
                priority=0.85,
                source="commitment",
                created_at=memory.minute,
                updated_at=0,
                deadline=deadline,
                progress="promised_before_epoch",
                evidence=[memory.id],
            )
        )
    return goals


def initial_goal_changes(agent: Agent):
    return [change("goals", goal.id, goal) for goal in initial_goals(agent)]


def active_goals(world, owner: str) -> list[dict]:
    return sorted(
        (row for row in world.owned("goals", owner) if row["status"] in ("active", "blocked")),
        key=lambda row: (-row["priority"], row["id"]),
    )


class Goals:
    def __init__(self, world):
        self.world = world

    def _validated(self, actor: Agent, request: GoalRequest, minute: int) -> tuple[Goal, str]:
        goal = Goal.model_validate(self.world.get("goals", request.goal_id))
        if goal.owner != actor.id:
            raise ValueError("I can change only my own goal")
        if goal.status in ("completed", "abandoned"):
            raise ValueError("that goal is already closed")
        transitions = {
            "revise": goal.status,
            "block": "blocked",
            "activate": "active",
            "complete": "completed",
            "abandon": "abandoned",
        }
        new_status = transitions[request.action]
        if request.action == "activate" and goal.status != "blocked":
            raise ValueError("only a blocked goal can be reactivated")
        if request.action == "block" and goal.status != "active":
            raise ValueError("only an active goal can be blocked")
        if request.deadline is not None and request.deadline < minute:
            raise ValueError("goal deadline cannot move into the past")
        known_evidence = {memory.id for memory in actor.memories}
        known_evidence.update(
            row["memory"]["id"] for row in self.world.owned("memory_archive", actor.id)
        )
        if set(request.evidence) - known_evidence:
            raise ValueError("goal evidence must come from my own memory")
        if request.action == "complete" and not request.evidence:
            raise ValueError("completion requires remembered evidence")
        if request.action == "complete":
            prerequisites = [
                Goal.model_validate(self.world.get("goals", identifier))
                for identifier in goal.prerequisites
            ]
            if any(item.owner != actor.id or item.status != "completed" for item in prerequisites):
                raise ValueError("goal prerequisites are not complete")
        return goal, new_status

    def validate(self, actor: Agent, request: GoalRequest, minute: int) -> None:
        self._validated(actor, request, minute)

    def transition_changes(self, actor: Agent, request: GoalRequest, minute: int):
        goal, new_status = self._validated(actor, request, minute)
        old_status = goal.status
        goal.status = new_status
        goal.updated_at = minute
        if request.description is not None:
            goal.description = request.description
        if request.priority is not None:
            goal.priority = request.priority
        if "deadline" in request.model_fields_set:
            goal.deadline = request.deadline
        if request.progress is not None:
            goal.progress = request.progress
        goal.evidence = list(dict.fromkeys([*goal.evidence, *request.evidence]))
        identifier = f"goal_history:{goal.id}:{minute}:{request.action}"
        transition = GoalTransition(
            id=identifier,
            goal_id=goal.id,
            owner=actor.id,
            minute=minute,
            action=request.action,
            old_status=old_status,
            new_status=new_status,
            reason=request.reason,
            evidence=request.evidence,
        )
        return [change("goals", goal.id, goal), change("goal_history", identifier, transition)]
