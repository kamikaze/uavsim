import asyncio
from collections import defaultdict
from typing import Any


class TopicBus:
    def __init__(self):
        self._subs: dict[str, list[asyncio.Queue]] = defaultdict(list)

    def subscribe(self, topic: str) -> asyncio.Queue:
        q: asyncio.Queue[Any] = asyncio.Queue()
        self._subs[topic].append(q)
        return q

    async def publish(self, topic: str, payload: Any):
        for q in list(self._subs.get(topic, [])):
            await q.put(payload)


# Global bus instance for simple wiring
bus = TopicBus()
