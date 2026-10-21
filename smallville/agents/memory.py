import re

from smallville.world.models import Agent, Memory

MAX_MEMORY = 128


def remember(
    agent: Agent,
    minute: int,
    text: str,
    source: str,
    importance: float = 0.5,
    kind: str = "episode",
) -> None:
    identifier = f"{agent.id}:{minute}:{source}:{len(agent.memories)}"
    agent.memories.append(
        Memory(
            id=identifier,
            minute=minute,
            text=text,
            source=source,
            importance=importance,
            kind=kind,
            last_access=minute,
        )
    )
    # Deliberately fallible, finite memory in Phase 1. The immutable event log
    # remains available to researchers, but is never given to an agent.
    agent.memories = agent.memories[-MAX_MEMORY:]


def retrieve(agent: Agent, query: str, minute: int, limit: int = 8) -> list[Memory]:
    if limit < 0:
        raise ValueError("negative retrieval limit")
    terms = set(re.findall(r"\w+", query.lower()))

    def score(memory):
        tokens = set(re.findall(r"\w+", memory.text.lower()))
        relevance = 0.05 + len(terms & tokens) / max(1, len(terms | tokens))
        recency = 0.995 ** (max(0, minute - memory.last_access) / 60)
        return recency * max(0.01, memory.importance) * relevance, memory.minute, memory.id

    result = sorted(agent.memories, key=score, reverse=True)[:limit]
    for memory in result:
        memory.last_access = minute
    return result
