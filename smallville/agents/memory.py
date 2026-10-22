from __future__ import annotations

import re
from hashlib import sha256
from typing import TYPE_CHECKING

from smallville.world.models import Agent, ArchivedMemory, Memory, change

if TYPE_CHECKING:
    from smallville.world.store import WorldState

MAX_MEMORY = 128


def remember(
    agent: Agent,
    minute: int,
    text: str,
    source: str,
    importance: float = 0.5,
    kind: str = "episode",
    evicted: list[Memory] | None = None,
) -> Memory:
    # Routine completion messages used to evict identity and benchmark evidence.
    # Coalesce identical recent outcomes while retaining that they recurred.
    if source == "gm_outcome":
        previous = next(
            (
                memory
                for memory in reversed(agent.memories)
                if memory.source == source and memory.text == text and minute - memory.minute <= 240
            ),
            None,
        )
        if previous:
            previous.minute = minute
            previous.last_access = minute
            previous.repetitions += 1
            return previous
    stem = f"{agent.id}:{minute}:{source}:{sha256(text.encode()).hexdigest()[:12]}"
    identifier = stem
    collision = 1
    known_ids = {item.id for item in agent.memories}
    while identifier in known_ids:
        identifier = f"{stem}:{collision}"
        collision += 1
    memory = Memory(
        id=identifier,
        minute=minute,
        text=text,
        source=source,
        importance=importance,
        kind=kind,
        last_access=minute,
    )
    agent.memories.append(memory)
    # Working memory stays finite and fallible, but identity seeds are durable.
    # Other entries compete on importance, access, kind and recency instead of
    # being deleted solely because 128 mundane outcomes arrived later.
    if len(agent.memories) > MAX_MEMORY:
        newest = minute

        def retention(item):
            protected = 100 if item.kind == "seed" else 0
            kind_bonus = 1.5 if item.kind == "reflection" else 0
            recency = max(0, 1 - (newest - max(item.minute, item.last_access)) / 10080)
            repetition = min(item.repetitions, 10) / 20
            return protected + 4 * item.importance + kind_bonus + recency + repetition

        keep = {m.id for m in sorted(agent.memories, key=retention, reverse=True)[:MAX_MEMORY]}
        removed = [m.model_copy(deep=True) for m in agent.memories if m.id not in keep]
        agent.memories = [m for m in agent.memories if m.id in keep]
        if evicted is not None:
            evicted.extend(removed)
    return memory


def _score(memory: Memory, query: str, terms: set[str], minute: int):
    tokens = set(re.findall(r"\w+", memory.text.lower()))
    relevance = len(terms & tokens) / max(1, len(terms | tokens))
    recency = 0.995 ** (max(0, minute - memory.last_access) / 60)
    phrase = 0.5 if query.lower() in memory.text.lower() else 0
    kind_bonus = 0.2 if memory.kind in ("seed", "reflection") else 0
    score = 3 * relevance + memory.importance + 0.35 * recency + phrase + kind_bonus
    return score, memory.minute, memory.id


def retrieve(agent: Agent, query: str, minute: int, limit: int = 8) -> list[Memory]:
    if limit < 0:
        raise ValueError("negative retrieval limit")
    terms = {term for term in re.findall(r"\w+", query.lower()) if len(term) > 1}
    result = sorted(
        agent.memories, key=lambda memory: _score(memory, query, terms, minute), reverse=True
    )[:limit]
    for memory in result:
        memory.last_access = minute
    return result


def archive_changes(owner: str, memories: list[Memory], minute: int):
    return [
        change(
            "memory_archive",
            memory.id,
            ArchivedMemory(
                id=memory.id,
                owner=owner,
                memory=memory,
                archived_at=minute,
            ),
        )
        for memory in memories
    ]


class LexicalMemoryRetriever:
    """Local lexical fallback over private working and archived memories."""

    name = "local_lexical_v1"

    def __init__(self, world: WorldState):
        self.world = world

    def retrieve(
        self, agent: Agent, query: str, minute: int, limit: int = 8
    ) -> list[tuple[Memory, str]]:
        if limit < 0:
            raise ValueError("negative retrieval limit")
        terms = {term for term in re.findall(r"\w+", query.lower()) if len(term) > 1}
        entries = [(memory, "working") for memory in agent.memories]
        entries.extend(
            (ArchivedMemory.model_validate(row).memory, "archive")
            for row in self.world.owned("memory_archive", agent.id)
        )
        entries.sort(
            key=lambda item: _score(item[0], query, terms, minute),
            reverse=True,
        )
        result = entries[:limit]
        for memory, store in result:
            if store == "working":
                memory.last_access = minute
        return result
