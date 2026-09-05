import os
import tempfile
from unittest.mock import MagicMock
from app.communication.heartbeat import HeartbeatEmitter
from app.communication.health_reporter import HealthReporter
from app.communication.offline_queue import DurableOfflineQueue


def test_heartbeat_payload_structure():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        queue = DurableOfflineQueue(db_path=db_path)
        mock_mqtt = MagicMock()
        mock_mqtt.device_id = "edge-001"
        mock_mqtt.store_id = "store_001"

        emitter = HeartbeatEmitter(
            mqtt_client=mock_mqtt,
            queue=queue,
            interval_seconds=15.0,
        )

        payload = emitter.build_payload()
        assert payload["deviceId"] == "edge-001"
        assert payload["storeId"] == "store_001"
        assert "timestamp" in payload
        assert "uptimeSeconds" in payload
        assert payload["status"] == "HEALTHY"
        assert payload["schemaVersion"] == "1.0"
        assert payload["queueDepth"] == 0
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_health_reporter_payload_structure():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        queue = DurableOfflineQueue(db_path=db_path)
        mock_mqtt = MagicMock()
        mock_mqtt.device_id = "edge-001"
        mock_mqtt.store_id = "store_001"

        reporter = HealthReporter(
            mqtt_client=mock_mqtt,
            queue=queue,
            interval_seconds=60.0,
        )

        payload = reporter.build_payload()
        assert payload["deviceId"] == "edge-001"
        assert payload["storeId"] == "store_001"
        assert "metrics" in payload
        assert "cpuPercent" in payload["metrics"]
        assert "cameras" in payload
        assert len(payload["cameras"]) > 0
        assert "models" in payload
        assert "queue" in payload
        assert payload["schemaVersion"] == "1.0"
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)
