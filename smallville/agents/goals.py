"""Durable, owner-scoped goals kept outside the fallible memory stream."""

from smallville.world.models import Agent, Goal, change


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
    return [
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


def initial_goal_changes(agent: Agent):
    return [change("goals", goal.id, goal) for goal in initial_goals(agent)]


def active_goals(world, owner: str) -> list[dict]:
    return sorted(
        (
            row
            for row in world.all("goals")
            if row["owner"] == owner and row["status"] in ("active", "blocked")
        ),
        key=lambda row: (-row["priority"], row["id"]),
    )
