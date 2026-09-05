"""Event dispatcher and background replay engine for Retail Intelligencia."""
import logging
import threading
import time
from typing import Any, Dict, Optional

from app.communication.mqtt_client import EdgeMQTTClient
from app.communication.offline_queue import DurableOfflineQueue
from app.events.models import RetailEvent

logger = logging.getLogger("communication.dispatcher")


class EventDispatcher:
    """Durably buffers RetailEvents and drains them to MQTT / backend with rate limiting."""

    def __init__(
        self,
        queue: DurableOfflineQueue,
        mqtt_client: EdgeMQTTClient,
        batch_size: int = 50,
        drain_rate_limit: int = 50,  # Max events per second
        poll_interval: float = 0.5,
    ):
        self.queue = queue
        self.mqtt_client = mqtt_client
        self.batch_size = batch_size
        self.drain_rate_limit = drain_rate_limit
        self.poll_interval = poll_interval

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._total_dispatched = 0
        self._total_acknowledged = 0

    def dispatch(self, event: RetailEvent) -> bool:
        """Entrypoint for retail rule engine. Durably persists the event to SQLite."""
        # Print event for local visibility / demo
        print(f"\n[{event.timestamp}] {event.eventType} (Zone: {event.zoneId}, Sev: {event.severity})")
        for k, v in event.metadata.items():
            print(f"  {k:<12}: {v}")
        print("-" * 35)

        enqueued = self.queue.enqueue(event)
        if enqueued:
            self._total_dispatched += 1
            logger.info(f"Dispatched event {event.eventId} to durable queue.")
        return enqueued

    def add(self, event: RetailEvent) -> bool:
        """Compatibility alias for LocalEventBuffer interface."""
        return self.dispatch(event)

    def start(self) -> None:
        """Start the background drain/replay worker."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._drain_loop, name="EventDispatcherDrain", daemon=True)
        self._thread.start()
        logger.info("Event dispatcher drain engine started.")

    def stop(self) -> None:
        """Gracefully stop the background worker."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        logger.info("Event dispatcher drain engine stopped.")

    def _drain_loop(self) -> None:
        min_interval = 1.0 / max(self.drain_rate_limit, 1)

        while self._running:
            if not self.mqtt_client.is_connected():
                time.sleep(self.poll_interval)
                continue

            # Fetch pending batch
            batch = self.queue.get_pending(limit=self.batch_size)
            if not batch:
                time.sleep(self.poll_interval)
                continue

            event_ids = [eid for eid, _ in batch]
            self.queue.mark_publishing(event_ids)

            for event_id, payload_json in batch:
                if not self._running or not self.mqtt_client.is_connected():
                    # Revert remaining publishing events on sudden disconnect
                    self.queue.reset_in_flight()
                    break

                def make_ack_callback(eid: str):
                    def _ack():
                        self.queue.mark_acknowledged(eid)
                        self._total_acknowledged += 1
                        logger.debug(f"Event {eid} acknowledged by broker/gateway.")
                    return _ack

                success, mid = self.mqtt_client.publish_channel(
                    channel="events",
                    payload=payload_json,
                    qos=1,
                    retain=False,
                    on_ack=make_ack_callback(event_id),
                )

                if not success:
                    logger.warning(f"Failed to publish event {event_id}; resetting status to PENDING.")
                    self.queue.mark_failed(event_id)

                # Rate limiting
                time.sleep(min_interval)

    def get_stats(self) -> Dict[str, Any]:
        q_stats = self.queue.get_stats()
        return {
            "total_dispatched": self._total_dispatched,
            "total_acknowledged": self._total_acknowledged,
            "queue": q_stats,
            "is_running": self._running,
        }
