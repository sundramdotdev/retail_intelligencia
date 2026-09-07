"""
In-memory live metrics store.

Thread-safe cache for the latest live metrics received from edge devices via MQTT.
The MQTT consumer updates this store; the /metrics/live endpoint reads from it.
The SSE broadcaster also pushes LIVE_METRICS events when this store updates.

Keyed by: (store_id, device_id)
"""
import logging
import threading
import time
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger("api.realtime.metrics_store")


class DeviceMetricsEntry:
    """Latest metrics snapshot for one device."""
    __slots__ = ("store_id", "device_id", "payload", "received_at")

    def __init__(self, store_id: str, device_id: str, payload: Dict[str, Any]):
        self.store_id = store_id
        self.device_id = device_id
        self.payload = payload
        self.received_at = time.time()

    @property
    def age_seconds(self) -> float:
        return time.time() - self.received_at

    @property
    def is_stale(self) -> bool:
        """Metrics are considered stale after 30 seconds without update."""
        return self.age_seconds > 30.0


class LiveMetricsStore:
    """Thread-safe in-memory store for live edge device metrics."""

    def __init__(self):
        self._lock = threading.Lock()
        self._store: Dict[Tuple[str, str], DeviceMetricsEntry] = {}

    def update(self, store_id: str, device_id: str, payload: Dict[str, Any]) -> None:
        """Update metrics for a device. Called from MQTT consumer thread."""
        key = (store_id, device_id)
        with self._lock:
            self._store[key] = DeviceMetricsEntry(store_id, device_id, payload)
        logger.debug(f"Live metrics updated for device={device_id} store={store_id}")

    def get_for_store(self, store_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the latest (non-stale) metrics for a store.

        Aggregates across all devices in the store. If multiple devices exist,
        picks the most recently updated one.
        """
        with self._lock:
            store_entries = [
                entry for (sid, _), entry in self._store.items()
                if sid == store_id and not entry.is_stale
            ]

        if not store_entries:
            return None

        # Use the most recently updated entry
        latest = max(store_entries, key=lambda e: e.received_at)
        return self._build_summary(latest)

    def get_for_device(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get latest metrics for a specific device."""
        with self._lock:
            for (_, did), entry in self._store.items():
                if did == device_id and not entry.is_stale:
                    return self._build_summary(entry)
        return None

    def _build_summary(self, entry: DeviceMetricsEntry) -> Dict[str, Any]:
        """Build a clean metrics summary from a raw MQTT payload."""
        p = entry.payload
        analytics = p.get("analytics", {})
        hardware = p.get("hardware", p.get("metrics", {}))
        vision = p.get("vision", {})
        camera = p.get("camera", p.get("cameras", [{}])[0] if p.get("cameras") else {})

        return {
            "deviceId": entry.device_id,
            "storeId": entry.store_id,
            "timestamp": p.get("timestamp"),
            "receivedAt": entry.received_at,
            "ageSeconds": round(entry.age_seconds, 1),
            "isStale": entry.is_stale,
            # Live analytics
            "peopleNow": analytics.get("peopleNow", 0),
            "footfallToday": analytics.get("footfallToday", 0),
            "footfallLastHour": analytics.get("footfallLastHour", 0),
            "footfallLast15Min": analytics.get("footfallLast15Min", 0),
            "averageDwellSeconds": analytics.get("averageDwellSeconds", 0),
            "longestDwellSeconds": analytics.get("longestDwellSeconds", 0),
            "activeObjects": analytics.get("activeObjects", 0),
            "objectsByClass": analytics.get("objectsByClass", {}),
            "zoneOccupancy": analytics.get("zoneOccupancy", {}),
            "dwellByZone": analytics.get("dwellByZone", {}),
            # Hardware
            "hardware": {
                "cpuPercent": hardware.get("cpuPercent", 0.0),
                "ramUsedMb": hardware.get("ramUsedMb", 0),
                "ramTotalMb": hardware.get("ramTotalMb", 0),
                "gpuPercent": hardware.get("gpuPercent", 0.0),
            },
            # Vision
            "vision": {
                "inferenceFps": vision.get("inferenceFps", 0.0),
                "latencyMs": vision.get("latencyMs", 0.0),
                "activeTracks": vision.get("activeTracks", 0),
                "model": vision.get("model", "yolo11n"),
            },
            # Camera
            "camera": {
                "id": camera.get("id", camera.get("cameraId", "camera-01")),
                "status": camera.get("status", "UNKNOWN"),
                "fps": camera.get("fps", 0.0),
            },
        }

    def all_device_ids(self, store_id: str):
        """List device IDs with live data for a store."""
        with self._lock:
            return [did for (sid, did) in self._store if sid == store_id]


# Singleton — shared between MQTT consumer and API routes
live_metrics_store = LiveMetricsStore()
