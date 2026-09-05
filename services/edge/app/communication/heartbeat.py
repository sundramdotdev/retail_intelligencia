"""Device heartbeat emitter for Retail Intelligencia Edge Node."""
from datetime import datetime, timezone
import json
import logging
import threading
import time
from typing import Any, Dict, Optional

from app.communication.mqtt_client import EdgeMQTTClient
from app.communication.offline_queue import DurableOfflineQueue

logger = logging.getLogger("communication.heartbeat")


class HeartbeatEmitter:
    """Emits periodic liveness ping to MQTT heartbeat topic."""

    def __init__(
        self,
        mqtt_client: EdgeMQTTClient,
        queue: DurableOfflineQueue,
        interval_seconds: float = 15.0,
        status_provider: Optional[Any] = None,
    ):
        self.mqtt_client = mqtt_client
        self.queue = queue
        self.interval_seconds = interval_seconds
        self.status_provider = status_provider

        self._start_time = time.time()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_heartbeat_at: Optional[float] = None
        self._last_payload: Optional[Dict[str, Any]] = None

    def build_payload(self) -> Dict[str, Any]:
        """Generate canonical heartbeat payload."""
        now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        uptime = int(time.time() - self._start_time)
        queue_stats = self.queue.get_stats()

        status = "HEALTHY"
        if self.status_provider and hasattr(self.status_provider, "get_status"):
            status = self.status_provider.get_status()

        return {
            "deviceId": self.mqtt_client.device_id,
            "storeId": self.mqtt_client.store_id,
            "timestamp": now_utc,
            "uptimeSeconds": uptime,
            "status": status,
            "queueDepth": queue_stats.get("pending", 0),
            "schemaVersion": "1.0",
        }

    def emit_once(self) -> bool:
        """Send a single heartbeat ping over MQTT (QoS 0)."""
        payload = self.build_payload()
        payload_json = json.dumps(payload)

        success, _ = self.mqtt_client.publish_channel(
            channel="heartbeat",
            payload=payload_json,
            qos=0,
            retain=False,
        )

        if success:
            self._last_heartbeat_at = time.time()
            self._last_payload = payload
            logger.debug(f"Heartbeat emitted successfully (queue depth: {payload['queueDepth']})")
        else:
            logger.debug("Failed to emit heartbeat (MQTT not connected)")

        return success

    def start(self) -> None:
        """Start heartbeat daemon thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, name="HeartbeatEmitter", daemon=True)
        self._thread.start()
        logger.info(f"Heartbeat emitter started with cadence: {self.interval_seconds}s")

    def stop(self) -> None:
        """Stop heartbeat daemon."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        logger.info("Heartbeat emitter stopped.")

    def _loop(self) -> None:
        while self._running:
            try:
                self.emit_once()
            except Exception as e:
                logger.error(f"Error during heartbeat emission: {e}")

            time.sleep(self.interval_seconds)

    def get_stats(self) -> Dict[str, Any]:
        return {
            "last_heartbeat_at": self._last_heartbeat_at,
            "last_payload": self._last_payload,
            "interval_seconds": self.interval_seconds,
            "is_running": self._running,
        }
