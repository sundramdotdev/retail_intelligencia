import time
from unittest.mock import MagicMock
from app.communication.mqtt_client import EdgeMQTTClient, MQTTConnectionState


def test_topic_builder():
    client = EdgeMQTTClient(
        broker_host="localhost",
        store_id="store_001",
        device_id="edge_001",
        environment="dev",
    )
    assert client.build_topic("events") == "retail/dev/store_001/edge_001/events"
    assert client.build_topic("heartbeat") == "retail/dev/store_001/edge_001/heartbeat"
    assert client.build_topic("health") == "retail/dev/store_001/edge_001/health"
    assert client.build_topic("config") == "retail/dev/store_001/edge_001/config"
    assert client.build_topic("control") == "retail/dev/store_001/edge_001/control"


def test_mqtt_state_transitions():
    client = EdgeMQTTClient(
        broker_host="localhost",
        store_id="store_001",
        device_id="edge_001",
        environment="dev",
    )
    assert client.get_state() == MQTTConnectionState.DISCONNECTED
    assert client.is_connected() is False

    # Simulate connection callback
    client._on_connect(None, None, None, 0)
    assert client.is_connected() is True
    assert client.get_state() == MQTTConnectionState.CONNECTED

    # Simulate disconnection callback while running
    client._running = True
    client._on_disconnect(None, None, 1)
    assert client.is_connected() is False
    assert client.get_state() == MQTTConnectionState.RECONNECTING


def test_publish_and_ack_callback():
    client = EdgeMQTTClient(
        broker_host="localhost",
        store_id="store_001",
        device_id="edge_001",
        environment="dev",
    )
    # Mock client and set connected
    client._state = MQTTConnectionState.CONNECTED
    mock_paho = MagicMock()
    mock_publish_info = MagicMock()
    mock_publish_info.mid = 42
    mock_paho.publish.return_value = mock_publish_info
    client._client = mock_paho

    ack_called = False

    def on_ack():
        nonlocal ack_called
        ack_called = True

    success, mid = client.publish_channel(
        channel="events",
        payload='{"test": 1}',
        qos=1,
        on_ack=on_ack,
    )

    assert success is True
    assert mid == 42
    assert ack_called is False

    # Simulate broker PUBACK for message id 42
    client._on_publish(None, None, 42)
    assert ack_called is True
