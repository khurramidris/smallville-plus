from smallville.world.models import Agent


def clamp(value: float, lower=0.0, upper=100.0) -> float:
    return round(max(lower, min(upper, value)), 6)


def advance_drives(agent: Agent, minute: int) -> None:
    elapsed = minute - agent.updated_at
    if elapsed < 0:
        raise ValueError("cannot age drives backwards")
    hours = elapsed / 60
    active = agent.activity
    needs = agent.needs
    decay = 0.5 ** (hours / 6) if hours else 1
    agent.emotion.social_valence = clamp(agent.emotion.social_valence * decay, -1, 1)
    agent.emotion.social_arousal = clamp(agent.emotion.social_arousal * decay, 0, 1)
    needs.fullness = clamp(needs.fullness - 3.8 * hours)
    needs.social = clamp(needs.social - (0.7 + agent.persona.sociability) * hours)
    needs.fun = clamp(
        needs.fun + (8 if active in ("leisure", "attend", "conversation") else -1.3) * hours
    )
    needs.energy = clamp(needs.energy + (9 if active == "sleep" else -4.1) * hours)
    if active in ("attend", "conversation"):
        needs.social = clamp(needs.social + 10 * hours)
    if min(needs.fullness, needs.energy) < 10:
        needs.health = clamp(needs.health - 1.5 * hours)
    elif active == "sleep":
        needs.health = clamp(needs.health + 0.4 * hours)
    base_valence = (needs.fullness + needs.social + needs.fun + needs.energy - 240) / 200
    agent.emotion.valence = clamp(base_valence + agent.emotion.social_valence, -1, 1)
    agent.emotion.arousal = clamp(
        (0.1 if active == "sleep" else 0.2 + (100 - needs.energy) / 160)
        + agent.emotion.social_arousal,
        0,
        1,
    )
    agent.emotion.label = (
        "tired"
        if needs.energy < 25
        else "hurt"
        if agent.emotion.social_valence < -0.25
        else "warm"
        if agent.emotion.social_valence > 0.25
        else "irritable"
        if agent.emotion.valence < -0.25
        else "content"
        if agent.emotion.valence > 0.2
        else "neutral"
    )
    agent.activity_minutes[active] = agent.activity_minutes.get(active, 0) + elapsed
    agent.updated_at = minute


def conversation_effect(agent: Agent, peer: str, body: str = "", *, affinity_delta: float = 0):
    """Apply an explicit legacy contact effect without inferring sentiment from text."""

    del body
    delta = clamp(affinity_delta, -0.15, 0.15)
    agent.relationships[peer] = clamp(agent.relationships.get(peer, 0) + delta, -1, 1)
    agent.needs.social = clamp(agent.needs.social + 2)
    agent.emotion.social_valence = clamp(agent.emotion.social_valence + delta, -1, 1)
    agent.emotion.social_arousal = clamp(agent.emotion.social_arousal + abs(delta), 0, 1)
    agent.emotion.valence = clamp(agent.emotion.valence + delta, -1, 1)
    agent.emotion.label = "annoyed" if delta < 0 else "engaged" if delta > 0 else "neutral"
