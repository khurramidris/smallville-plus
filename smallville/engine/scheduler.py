from __future__ import annotations

import heapq
from collections import defaultdict
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from smallville.engine.events import Event


@dataclass(order=True)
class Scheduled:
    minute: int
    priority: int
    sequence: int
    kind: str = field(compare=False)
    agent: str | None = field(default=None, compare=False)
    data: dict[str, Any] = field(default_factory=dict, compare=False)


class Scheduler:
    def __init__(self):
        self.queue: list[Scheduled] = []
        self.sequence = 0
        self.conditions: dict[str, tuple[Callable[[], bool], str, str | None]] = {}

    def schedule(self, minute: int, kind: str, agent: str | None = None,
                 data: dict | None = None, priority: int = 10) -> None:
        if minute < 0:
            raise ValueError("negative event time")
        self.sequence += 1
        heapq.heappush(self.queue, Scheduled(minute, priority, self.sequence, kind, agent, data or {}))

    def when(self, key: str, predicate: Callable[[], bool], kind: str, agent: str | None = None):
        self.conditions[key] = (predicate, kind, agent)

    def check_conditions(self, minute: int):
        for key, (predicate, kind, agent) in list(self.conditions.items()):
            if predicate():
                self.schedule(minute, kind, agent)
                del self.conditions[key]

    def pop(self) -> Scheduled:
        return heapq.heappop(self.queue)


class EventBus:
    def __init__(self):
        self.subscribers: dict[str, list[Callable[[Event], Awaitable[None]]]] = defaultdict(list)

    def subscribe(self, kind: str, callback: Callable[[Event], Awaitable[None]]):
        self.subscribers[kind].append(callback)

    async def publish(self, event: Event):
        # Preserve order; subscribers do not race the authoritative writer.
        for callback in [*self.subscribers[event.kind], *self.subscribers["*"]]:
            await callback(event)
