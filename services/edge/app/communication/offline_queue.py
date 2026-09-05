"""Durable, offline-first SQLite event queue for edge nodes."""
from contextlib import contextmanager
import json
import logging
import os
import sqlite3
import time
from typing import Any, Dict, List, Optional, Tuple

from app.events.models import RetailEvent

logger = logging.getLogger("communication.queue")


class DeliveryStatus:
    PENDING = "PENDING"
    PUBLISHING = "PUBLISHING"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    FAILED = "FAILED"


class DurableOfflineQueue:
    """Thread-safe, crash-resilient SQLite WAL event queue."""

    def __init__(
        self,
        db_path: str = "data/event_queue.db",
        max_events: int = 10000,
        max_storage_mb: float = 100.0,
        max_retries: int = 5,
    ):
        self.db_path = db_path
        self.max_events = max_events
        self.max_storage_bytes = int(max_storage_mb * 1024 * 1024)
        self.max_retries = max_retries

        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        self._init_db()

    @contextmanager
    def _connection(self):
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        """Initialize database schema and set WAL mode for concurrency."""
        with self._connection() as conn:
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA synchronous = NORMAL;")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS event_queue (
                    event_id TEXT PRIMARY KEY,
                    store_id TEXT NOT NULL,
                    device_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'PENDING',
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_event_queue_status_created 
                ON event_queue (status, created_at ASC);
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_event_queue_event_id 
                ON event_queue (event_id);
                """
            )
            # Crash recovery: reset any stuck in-flight PUBLISHING events back to PENDING
            conn.execute(
                """
                UPDATE event_queue 
                SET status = 'PENDING', updated_at = ? 
                WHERE status = 'PUBLISHING';
                """,
                (time.time(),),
            )
            conn.commit()

    def enqueue(self, event: RetailEvent) -> bool:
        """Duraly enqueue a canonical RetailEvent."""
        self._enforce_capacity()

        now = time.time()
        payload_json = (
            event.model_dump_json()
            if hasattr(event, "model_dump_json")
            else json.dumps(event.dict())
        )

        with self._connection() as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO event_queue (
                        event_id, store_id, device_id, event_type, 
                        timestamp, payload, status, retry_count, 
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?);
                    """,
                    (
                        event.eventId,
                        event.storeId,
                        event.deviceId,
                        event.eventType,
                        event.timestamp,
                        payload_json,
                        DeliveryStatus.PENDING,
                        now,
                        now,
                    ),
                )
                conn.commit()
                logger.debug(f"Enqueued event {event.eventId} (status: PENDING)")
                return True
            except sqlite3.IntegrityError:
                logger.warning(f"Event {event.eventId} already present in local queue; skipping duplicate enqueue.")
                return False

    def get_pending(self, limit: int = 50) -> List[Tuple[str, str]]:
        """Retrieve the next batch of PENDING events in strict FIFO order (event_id, payload_json)."""
        with self._connection() as conn:
            cursor = conn.execute(
                """
                SELECT event_id, payload FROM event_queue
                WHERE status = 'PENDING'
                ORDER BY created_at ASC
                LIMIT ?;
                """,
                (limit,),
            )
            return [(row["event_id"], row["payload"]) for row in cursor.fetchall()]

    def mark_publishing(self, event_ids: List[str]) -> None:
        """Mark a batch of events as in-flight publishing."""
        if not event_ids:
            return
        now = time.time()
        with self._connection() as conn:
            placeholders = ",".join("?" for _ in event_ids)
            conn.execute(
                f"""
                UPDATE event_queue
                SET status = '{DeliveryStatus.PUBLISHING}', updated_at = ?
                WHERE event_id IN ({placeholders});
                """,
                [now] + event_ids,
            )
            conn.commit()

    def mark_acknowledged(self, event_id: str) -> bool:
        """Mark an event as successfully delivered and acknowledged by backend."""
        now = time.time()
        with self._connection() as conn:
            cursor = conn.execute(
                f"""
                UPDATE event_queue
                SET status = '{DeliveryStatus.ACKNOWLEDGED}', updated_at = ?
                WHERE event_id = ?;
                """,
                (now, event_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def mark_failed(self, event_id: str, max_retries: Optional[int] = None) -> None:
        """Increment retry count. If below threshold, requeue as PENDING; otherwise mark FAILED."""
        retries_limit = max_retries if max_retries is not None else self.max_retries
        now = time.time()
        with self._connection() as conn:
            conn.execute(
                """
                UPDATE event_queue
                SET retry_count = retry_count + 1,
                    status = CASE 
                        WHEN retry_count + 1 >= ? THEN 'FAILED' 
                        ELSE 'PENDING' 
                    END,
                    updated_at = ?
                WHERE event_id = ?;
                """,
                (retries_limit, now, event_id),
            )
            conn.commit()

    def reset_in_flight(self) -> int:
        """Reset any events currently in PUBLISHING state back to PENDING (e.g. on reconnect)."""
        now = time.time()
        with self._connection() as conn:
            cursor = conn.execute(
                f"""
                UPDATE event_queue
                SET status = '{DeliveryStatus.PENDING}', updated_at = ?
                WHERE status = '{DeliveryStatus.PUBLISHING}';
                """,
                (now,),
            )
            conn.commit()
            return cursor.rowcount

    def purge_acknowledged(self, older_than_seconds: float = 3600.0) -> int:
        """Purge acknowledged events older than a given duration to free disk space."""
        cutoff = time.time() - older_than_seconds
        with self._connection() as conn:
            cursor = conn.execute(
                f"""
                DELETE FROM event_queue
                WHERE status = '{DeliveryStatus.ACKNOWLEDGED}' AND updated_at < ?;
                """,
                (cutoff,),
            )
            conn.commit()
            return cursor.rowcount

    def _enforce_capacity(self) -> None:
        """Enforce maximum queue depth and storage bounds using oldest-first eviction."""
        stats = self.get_stats()
        total_count = stats["total"]
        storage_bytes = stats["storage_bytes"]

        if total_count < self.max_events and storage_bytes < self.max_storage_bytes:
            return

        with self._connection() as conn:
            # 1. First evict oldest acknowledged events
            conn.execute(
                f"""
                DELETE FROM event_queue
                WHERE event_id IN (
                    SELECT event_id FROM event_queue
                    WHERE status = '{DeliveryStatus.ACKNOWLEDGED}'
                    ORDER BY created_at ASC
                    LIMIT 200
                );
                """
            )
            conn.commit()

            # 2. Check if still exceeding bounds; if so, evict oldest pending with explicit warning
            cursor = conn.execute("SELECT COUNT(*) as count FROM event_queue;")
            remaining = cursor.fetchone()["count"]
            if remaining >= self.max_events:
                evict_count = (remaining - self.max_events) + 50
                logger.warning(
                    f"Queue capacity critical ({remaining}/{self.max_events} events). "
                    f"Evicting {evict_count} oldest unacknowledged events to protect system stability."
                )
                conn.execute(
                    """
                    DELETE FROM event_queue
                    WHERE event_id IN (
                        SELECT event_id FROM event_queue
                        ORDER BY created_at ASC
                        LIMIT ?
                    );
                    """,
                    (evict_count,),
                )
                conn.commit()

    def get_stats(self) -> Dict[str, Any]:
        """Return comprehensive metrics about current queue health and depth."""
        storage_bytes = 0
        if os.path.exists(self.db_path):
            storage_bytes = os.path.getsize(self.db_path)
            wal_path = f"{self.db_path}-wal"
            if os.path.exists(wal_path):
                storage_bytes += os.path.getsize(wal_path)

        with self._connection() as conn:
            cursor = conn.execute(
                """
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'PENDING' THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN status = 'PUBLISHING' THEN 1 ELSE 0 END) as publishing,
                    SUM(CASE WHEN status = 'ACKNOWLEDGED' THEN 1 ELSE 0 END) as acknowledged,
                    SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as failed,
                    MIN(CASE WHEN status = 'PENDING' THEN created_at ELSE NULL END) as oldest_pending_timestamp
                FROM event_queue;
                """
            )
            row = cursor.fetchone()
            return {
                "total": row["total"] or 0,
                "pending": row["pending"] or 0,
                "publishing": row["publishing"] or 0,
                "acknowledged": row["acknowledged"] or 0,
                "failed": row["failed"] or 0,
                "oldest_pending_timestamp": row["oldest_pending_timestamp"],
                "storage_bytes": storage_bytes,
                "storage_mb": round(storage_bytes / (1024 * 1024), 2),
            }
