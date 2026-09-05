import os
import tempfile
import time
import pytest
from app.communication.offline_queue import DurableOfflineQueue, DeliveryStatus
from app.events.models import RetailEvent, SourceMetadata


def create_sample_event(event_id: str, event_type: str = "QUEUE_HIGH") -> RetailEvent:
    return RetailEvent(
        eventId=event_id,
        eventVersion="1.0",
        eventType=event_type,
        deviceId="edge_001",
        storeId="store_001",
        zoneId="zone_checkout_01",
        timestamp="2026-09-06T10:00:00Z",
        confidence=0.95,
        severity="HIGH",
        metadata={"queueCount": 5, "threshold": 3},
        source=SourceMetadata(cameraId="cam_01", modelId="yolo11n", modelVersion="1.0.0"),
        schemaVersion="1.0",
    )


def test_enqueue_and_fifo_order():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        queue = DurableOfflineQueue(db_path=db_path)
        e1 = create_sample_event("evt_01J00000000000000000000001")
        time.sleep(0.01)
        e2 = create_sample_event("evt_01J00000000000000000000002")
        time.sleep(0.01)
        e3 = create_sample_event("evt_01J00000000000000000000003")

        assert queue.enqueue(e1) is True
        assert queue.enqueue(e2) is True
        assert queue.enqueue(e3) is True

        pending = queue.get_pending(limit=10)
        assert len(pending) == 3
        # Assert FIFO ordering
        assert pending[0][0] == "evt_01J00000000000000000000001"
        assert pending[1][0] == "evt_01J00000000000000000000002"
        assert pending[2][0] == "evt_01J00000000000000000000003"
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_persistence_across_process_restarts():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        # Instance 1: Enqueue an event and set it to publishing (simulating active network during crash)
        q1 = DurableOfflineQueue(db_path=db_path)
        e = create_sample_event("evt_01J98X7Z8K3M0W4V8R9N1P2Q3R")
        q1.enqueue(e)
        q1.mark_publishing(["evt_01J98X7Z8K3M0W4V8R9N1P2Q3R"])
        del q1

        # Instance 2: Simulate process reboot
        q2 = DurableOfflineQueue(db_path=db_path)
        stats = q2.get_stats()
        # In-flight publishing event must be automatically reset to PENDING on startup
        assert stats["pending"] == 1
        assert stats["publishing"] == 0

        pending = q2.get_pending(limit=5)
        assert len(pending) == 1
        assert pending[0][0] == "evt_01J98X7Z8K3M0W4V8R9N1P2Q3R"

        # Mark acknowledged
        q2.mark_acknowledged("evt_01J98X7Z8K3M0W4V8R9N1P2Q3R")
        assert q2.get_stats()["acknowledged"] == 1
        assert q2.get_stats()["pending"] == 0
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_capacity_bounds_and_oldest_eviction():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        # Small max_events = 5
        queue = DurableOfflineQueue(db_path=db_path, max_events=5)
        for i in range(10):
            e = create_sample_event(f"evt_01J0000000000000000000000{i}")
            queue.enqueue(e)

        stats = queue.get_stats()
        # Queue should enforce capacity and prevent unbounded growth
        assert stats["total"] <= 5
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)


def test_duplicate_enqueue_protection():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        queue = DurableOfflineQueue(db_path=db_path)
        e = create_sample_event("evt_01J99999999999999999999999")
        assert queue.enqueue(e) is True
        # Re-enqueuing the same eventId must return False and not duplicate
        assert queue.enqueue(e) is False
        assert queue.get_stats()["total"] == 1
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)
