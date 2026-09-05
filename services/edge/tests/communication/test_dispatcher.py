import os
import tempfile
import time
from unittest.mock import MagicMock
from app.communication.dispatcher import EventDispatcher
from app.communication.offline_queue import DurableOfflineQueue
from app.events.models import RetailEvent, SourceMetadata


def create_sample_event(event_id: str) -> RetailEvent:
    return RetailEvent(
        eventId=event_id,
        eventVersion="1.0",
        eventType="SHELF_LOW_STOCK",
        deviceId="edge_001",
        storeId="store_001",
        zoneId="zone_aisle_01",
        timestamp="2026-09-06T10:00:00Z",
        confidence=0.92,
        severity="MEDIUM",
        metadata={"occupancyPercentage": 20.0, "threshold": 25.0},
        source=SourceMetadata(cameraId="cam_01", modelId="yolo11n", modelVersion="1.0.0"),
        schemaVersion="1.0",
    )


def test_dispatcher_offline_buffering_and_drain():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        queue = DurableOfflineQueue(db_path=db_path)
        mock_mqtt = MagicMock()
        mock_mqtt.is_connected.return_value = False  # Offline initially

        dispatcher = EventDispatcher(
            queue=queue,
            mqtt_client=mock_mqtt,
            batch_size=10,
            poll_interval=0.05,
        )

        # 1. Dispatch 3 events while offline
        e1 = create_sample_event("evt_01J_DISP_001")
        e2 = create_sample_event("evt_01J_DISP_002")
        e3 = create_sample_event("evt_01J_DISP_003")

        dispatcher.dispatch(e1)
        dispatcher.dispatch(e2)
        dispatcher.dispatch(e3)

        # Verify events are stored in durable queue
        stats = queue.get_stats()
        assert stats["pending"] == 3
        assert stats["acknowledged"] == 0

        # Start drain loop
        dispatcher.start()
        time.sleep(0.1)

        # While offline, events remain pending in queue
        assert queue.get_stats()["pending"] == 3

        # 2. Simulate network restoration
        mock_mqtt.is_connected.return_value = True

        def fake_publish_channel(channel, payload, qos=1, retain=False, on_ack=None):
            if on_ack:
                on_ack()  # Simulate instantaneous ACK
            return True, 100

        mock_mqtt.publish_channel.side_effect = fake_publish_channel

        # Wait for drain loop to process
        time.sleep(0.3)
        dispatcher.stop()

        # All 3 events should now be drained and marked ACKNOWLEDGED
        stats_after = queue.get_stats()
        assert stats_after["acknowledged"] == 3
        assert stats_after["pending"] == 0
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)
