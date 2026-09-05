"""In-memory event broadcaster for SSE connections.

Store-scoped event distribution to connected dashboard clients.
No external infrastructure required (no Redis for MVP).
"""
import asyncio
import logging
import json
from typing import Any, Dict, Optional, Set
from dataclasses import dataclass, field

logger = logging.getLogger("api.realtime.broadcaster")


@dataclass
class SSEConnection:
    """Represents a single SSE client connection."""
    store_id: str
    user_id: str
    role: str
    queue: asyncio.Queue = field(default_factory=lambda: asyncio.Queue(maxsize=256))


class EventBroadcaster:
    """Manages SSE connections and broadcasts store-scoped events.

    Thread-safe for use from both MQTT consumer thread and async FastAPI handlers.
    """

    def __init__(self):
        self._connections: Dict[str, Set[SSEConnection]] = {}
        self._lock = asyncio.Lock()
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Set the event loop for cross-thread broadcasting."""
        self._loop = loop

    async def subscribe(self, store_id: str, user_id: str, role: str) -> SSEConnection:
        """Register a new SSE client connection for a store."""
        conn = SSEConnection(store_id=store_id, user_id=user_id, role=role)
        async with self._lock:
            if store_id not in self._connections:
                self._connections[store_id] = set()
            self._connections[store_id].add(conn)
        logger.info(f"SSE client subscribed: store={store_id} user={user_id} role={role} (total={self.connection_count(store_id)})")
        return conn

    async def unsubscribe(self, conn: SSEConnection) -> None:
        """Remove an SSE client connection."""
        async with self._lock:
            store_conns = self._connections.get(conn.store_id)
            if store_conns:
                store_conns.discard(conn)
                if not store_conns:
                    del self._connections[conn.store_id]
        logger.info(f"SSE client unsubscribed: store={conn.store_id} user={conn.user_id}")

    async def broadcast(self, store_id: str, event_type: str, data: Dict[str, Any]) -> int:
        """Broadcast an event to all SSE clients subscribed to a store.

        Returns the number of clients that received the event.
        """
        message = {
            "type": event_type,
            **data,
        }
        serialized = json.dumps(message)
        sent = 0

        async with self._lock:
            store_conns = self._connections.get(store_id, set()).copy()

        stale: list = []
        for conn in store_conns:
            try:
                conn.queue.put_nowait(serialized)
                sent += 1
            except asyncio.QueueFull:
                logger.warning(f"SSE queue full for user={conn.user_id}, dropping connection")
                stale.append(conn)

        # Clean up stale connections
        for conn in stale:
            await self.unsubscribe(conn)

        if sent > 0:
            logger.debug(f"Broadcast {event_type} to {sent} clients in store={store_id}")
        return sent

    def broadcast_sync(self, store_id: str, event_type: str, data: Dict[str, Any]) -> None:
        """Thread-safe broadcast for use from MQTT consumer thread."""
        if self._loop and not self._loop.is_closed():
            asyncio.run_coroutine_threadsafe(
                self.broadcast(store_id, event_type, data),
                self._loop,
            )

    def connection_count(self, store_id: Optional[str] = None) -> int:
        """Get the number of active SSE connections."""
        if store_id:
            return len(self._connections.get(store_id, set()))
        return sum(len(conns) for conns in self._connections.values())

    @property
    def total_connections(self) -> int:
        return self.connection_count()


# Singleton broadcaster instance
broadcaster = EventBroadcaster()
