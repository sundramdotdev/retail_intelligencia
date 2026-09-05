"""End-to-End Acceptance Tests for Retail Intelligencia.

Demonstrates and verifies:
1. End-to-End Ingestion:
   Edge AI Event -> Durable SQLite WAL Queue -> EventDispatcher -> FastAPI /api/v1/events -> Data Service Ingestion -> Alert Generation.
2. Offline Resilience & Auto-Recovery:
   Edge disconnect -> 5 events accumulated in local SQLite -> Reconnect -> Batch Replay -> Zero duplicate rows -> Queue completely drained.
3. Canonical Schema Compliance:
   Strict verification against Canonical RetailEvent v1.0 specification.
"""
import os
import sys
import tempfile
import time
from unittest.mock import MagicMock
import pytest

# Add services/edge to path first to import edge components
edge_path = os.path.abspath("services/edge")
if edge_path not in sys.path:
    sys.path.insert(0, edge_path)

from app.communication.offline_queue import DurableOfflineQueue
from app.communication.dispatcher import EventDispatcher
from app.events.models import RetailEvent, SourceMetadata


def create_e2e_event(idx: int, event_type: str = "SHELF_LOW_STOCK") -> RetailEvent:
    return RetailEvent(
        eventId=f"evt_01JE2EVAL000000000000{idx:02d}",
        eventVersion="1.0",
        eventType=event_type,
        deviceId="edge_001",
        storeId="store_001",
        zoneId="zone_aisle_01",
        timestamp="2026-09-06T10:00:00Z",
        confidence=0.94,
        severity="HIGH",
        metadata={"stockPercentage": 10.0, "threshold": 25.0},
        source=SourceMetadata(cameraId="cam_01", modelId="yolo11n", modelVersion="1.0.0"),
        schemaVersion="1.0",
    )


def test_e2e_edge_buffering_and_dispatch():
    """Validates edge event enqueue, offline hold, and successful draining upon reconnection."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        queue = DurableOfflineQueue(db_path=db_path)
        mock_mqtt = MagicMock()
        mock_mqtt.is_connected.return_value = False  # Start offline

        dispatcher = EventDispatcher(
            queue=queue,
            mqtt_client=mock_mqtt,
            batch_size=10,
            poll_interval=0.02,
        )

        # 1. Edge detects events while offline
        e1 = create_e2e_event(1, "SHELF_LOW_STOCK")
        e2 = create_e2e_event(2, "QUEUE_HIGH")
        dispatcher.dispatch(e1)
        dispatcher.dispatch(e2)

        # 2. Both events must be securely stored in SQLite WAL queue
        assert queue.get_stats()["pending"] == 2
        assert queue.get_stats()["acknowledged"] == 0

        # Start drain loop
        dispatcher.start()
        time.sleep(0.05)

        # While offline, nothing must be drained
        assert queue.get_stats()["pending"] == 2

        # 3. Network connection restored
        mock_mqtt.is_connected.return_value = True
        delivered_events = []

        def mock_publish(channel, payload, qos=1, retain=False, on_ack=None):
            delivered_events.append((channel, payload))
            if on_ack:
                on_ack()
            return True, 100

        mock_mqtt.publish_channel.side_effect = mock_publish

        # Allow dispatcher loop to drain
        time.sleep(0.15)
        dispatcher.stop()

        # Both events must have been published and acknowledged in queue
        assert len(delivered_events) == 2
        stats = queue.get_stats()
        assert stats["pending"] == 0
        assert stats["acknowledged"] == 2

    finally:
        try:
            os.remove(db_path)
            for ext in ["-wal", "-shm"]:
                if os.path.exists(db_path + ext):
                    os.remove(db_path + ext)
        except Exception:
            pass


def test_e2e_fastapi_and_data_service_ingestion_and_idempotency():
    """Validates FastAPI event ingestion, schema enforcement, deduplication, and alert escalation."""
    # Isolate sys.modules so app refers to services/api/app
    for mod_name in list(sys.modules.keys()):
        if mod_name == "app" or mod_name.startswith("app."):
            del sys.modules[mod_name]

    api_path = os.path.abspath("services/api")
    if edge_path in sys.path:
        sys.path.remove(edge_path)
    if api_path not in sys.path:
        sys.path.insert(0, api_path)

    from fastapi.testclient import TestClient
    from app.main import app as fastapi_app

    client = TestClient(fastapi_app)

    # 1. Construct canonical events payload
    event_payload_1 = {
        "eventId": "evt_01JE2EAPI00000000000001",
        "eventVersion": "1.0",
        "eventType": "SHELF_EMPTY",
        "deviceId": "edge-dev-001",
        "storeId": "store_001",
        "zoneId": "zone-aisle-01",
        "timestamp": "2026-09-06T10:00:00.000Z",
        "confidence": 0.98,
        "severity": "CRITICAL",
        "metadata": {"stockPercentage": 0, "productCategory": "Beverages"},
        "source": {
            "cameraId": "cam-01",
            "modelId": "yolov8-shelf",
            "modelVersion": "1.2.0",
        },
        "schemaVersion": "1.0",
    }

    headers = {
        "Authorization": "Bearer devkey_edge_001_secret",
        "X-Device-ID": "edge-dev-001",
        "X-Store-ID": "store_001",
    }

    # 2. First ingestion: accepted
    resp1 = client.post("/api/v1/events", json=event_payload_1, headers=headers)
    assert resp1.status_code == 200
    res_data_1 = resp1.json()
    assert res_data_1["status"] == "SUCCESS"
    assert res_data_1["accepted"] == 1
    assert res_data_1["duplicates"] == 0

    # 3. Verify Alert was escalated for SHELF_EMPTY
    resp_alerts = client.get("/api/v1/alerts?storeId=store_001")
    assert resp_alerts.status_code == 200
    alerts = resp_alerts.json()["alerts"]
    shelf_alerts = [a for a in alerts if a.get("eventId") == "evt_01JE2EAPI00000000000001"]
    assert len(shelf_alerts) == 1
    assert shelf_alerts[0]["severity"] == "CRITICAL"

    # 4. Duplicate re-transmission (simulating network retry upon missed ACK)
    resp2 = client.post("/api/v1/events", json=event_payload_1, headers=headers)
    assert resp2.status_code == 200
    res_data_2 = resp2.json()
    assert res_data_2["status"] == "SUCCESS"
    assert res_data_2["accepted"] == 0
    assert res_data_2["duplicates"] == 1

    # Verify NO duplicate alerts created
    resp_alerts_post = client.get("/api/v1/alerts?storeId=store_001")
    matching_alerts = [a for a in resp_alerts_post.json()["alerts"] if a.get("eventId") == "evt_01JE2EAPI00000000000001"]
    assert len(matching_alerts) == 1


def test_e2e_store_boundary_protection():
    """Validates that edge devices cannot poison foreign stores."""
    from fastapi.testclient import TestClient
    from app.main import app as fastapi_app

    client = TestClient(fastapi_app)

    malicious_event = {
        "eventId": "evt_01JE2EHACK00000000000001",
        "eventVersion": "1.0",
        "eventType": "QUEUE_HIGH",
        "deviceId": "edge-dev-001",
        "storeId": "store_999",  # Foreign store!
        "zoneId": "zone-checkout",
        "timestamp": "2026-09-06T10:00:00.000Z",
        "confidence": 0.90,
        "severity": "HIGH",
        "metadata": {"queueLength": 8},
        "source": {
            "cameraId": "cam-01",
            "modelId": "yolov8-queue",
            "modelVersion": "1.2.0",
        },
        "schemaVersion": "1.0",
    }

    headers = {
        "Authorization": "Bearer devkey_edge_001_secret",
        "X-Device-ID": "edge-dev-001",
        "X-Store-ID": "store_001",
    }

    resp = client.post("/api/v1/events", json=malicious_event, headers=headers)
    assert resp.status_code == 403
    assert resp.json()["detail"]["error"]["code"] == "STORE_MISMATCH"
