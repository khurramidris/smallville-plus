from smallville.apps.phone import Messaging
from smallville.world.models import Agent
from smallville.world.store import WorldState


def perceive(world: WorldState, agent: Agent, minute: int) -> dict:
    """Only public co-located activity and this person's phone; never other minds."""
    peers = (
        []
        if agent.location is None
        else [
            {"id": other.id, "name": other.persona.name, "activity": other.activity}
            for other in world.at(agent.location)
            if other.id != agent.id
        ]
    )
    return {
        "minute": minute,
        "location": agent.location,
        "nearby": peers,
        "notifications": Messaging(world).notifications(agent.id, "verbose"),
    }
