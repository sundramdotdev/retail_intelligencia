"""Thread-safe resilient MQTT client for Retail Intelligencia Edge Node."""
import logging
import ssl
import threading
import time
from typing import Any, Callable, Dict, Optional, Set

try:
    import paho.mqtt.client as mqtt
except ImportError:
    mqtt = None

logger = logging.getLogger("communication.mqtt")


class MQTTConnectionState:
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    RECONNECTING = "RECONNECTING"
    ERROR = "ERROR"


class EdgeMQTTClient:
    """Manages secure MQTT connectivity, exponential backoff, and topic isolation."""

    def __init__(
        self,
        broker_host: str = "localhost",
        broker_port: int = 1883,
        client_id: str = "edge-dev-001",
        store_id: str = "store_001",
        device_id: str = "edge-dev-001",
        environment: str = "dev",
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_tls: bool = False,
        ca_certs: Optional[str] = None,
        certfile: Optional[str] = None,
        keyfile: Optional[str] = None,
        keepalive: int = 30,
        initial_retry_delay: float = 1.0,
        max_retry_delay: float = 60.0,
    ):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client_id = client_id
        self.store_id = store_id
        self.device_id = device_id
        self.environment = environment
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.ca_certs = ca_certs
        self.certfile = certfile
        self.keyfile = keyfile
        self.keepalive = keepalive
        self.initial_retry_delay = initial_retry_delay
        self.max_retry_delay = max_retry_delay

        self._state = MQTTConnectionState.DISCONNECTED
        self._client: Optional[Any] = None
        self._lock = threading.Lock()
        self._current_retry_delay = initial_retry_delay
        self._reconnect_thread: Optional[threading.Thread] = None
        self._running = False
        self._last_connected_at: Optional[float] = None
        self._last_published_at: Optional[float] = None
        self._last_ack_at: Optional[float] = None

        # Tracking message acknowledgements: mid -> callback
        self._in_flight_acks: Dict[int, Callable[[], None]] = {}
        self._subscriptions: Dict[str, Callable[[str, bytes], None]] = {}

        self._init_paho_client()

    def _init_paho_client(self) -> None:
        if mqtt is None:
            logger.warning("paho-mqtt is not installed; MQTT client running in simulation/noop mode.")
            return

        # paho-mqtt v2.x compatibility
        if hasattr(mqtt, "CallbackAPIVersion"):
            self._client = mqtt.Client(
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                client_id=self.client_id,
                clean_session=False,
            )
        else:
            self._client = mqtt.Client(client_id=self.client_id, clean_session=False)

        if self.username:
            self._client.username_pw_set(self.username, self.password)

        if self.use_tls:
            tls_context = ssl.create_default_context(
                cafile=self.ca_certs if self.ca_certs else None
            )
            if self.certfile and self.keyfile:
                tls_context.load_cert_chain(self.certfile, self.keyfile)
            self._client.tls_set_context(tls_context)

        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_publish = self._on_publish
        self._client.on_message = self._on_message

    def build_topic(self, channel: str) -> str:
        """Enforce canonical topic namespace: retail/{env}/{storeId}/{deviceId}/{channel}"""
        return f"retail/{self.environment}/{self.store_id}/{self.device_id}/{channel}"

    def connect(self) -> bool:
        """Connect to broker and start background network loop."""
        if mqtt is None or self._client is None:
            self._state = MQTTConnectionState.ERROR
            return False

        with self._lock:
            self._running = True
            self._state = MQTTConnectionState.CONNECTING

        try:
            logger.info(f"Connecting to MQTT broker {self.broker_host}:{self.broker_port} (TLS: {self.use_tls})...")
            self._client.connect_async(self.broker_host, self.broker_port, self.keepalive)
            self._client.loop_start()
            return True
        except Exception as e:
            logger.error(f"Failed to initiate MQTT connection: {e}")
            with self._lock:
                self._state = MQTTConnectionState.ERROR
            self._schedule_reconnect()
            return False

    def disconnect(self) -> None:
        """Gracefully disconnect from the MQTT broker."""
        with self._lock:
            self._running = False
            self._state = MQTTConnectionState.DISCONNECTED

        if self._client:
            try:
                self._client.loop_stop()
                self._client.disconnect()
            except Exception as e:
                logger.debug(f"Exception during disconnect: {e}")

    def is_connected(self) -> bool:
        with self._lock:
            return self._state == MQTTConnectionState.CONNECTED

    def get_state(self) -> str:
        with self._lock:
            return self._state

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "state": self._state,
                "broker": f"{self.broker_host}:{self.broker_port}",
                "tls": self.use_tls,
                "last_connected_at": self._last_connected_at,
                "last_published_at": self._last_published_at,
                "last_ack_at": self._last_ack_at,
                "in_flight_count": len(self._in_flight_acks),
            }

    def publish_channel(
        self,
        channel: str,
        payload: str,
        qos: int = 1,
        retain: bool = False,
        on_ack: Optional[Callable[[], None]] = None,
    ) -> Tuple[bool, Optional[int]]:
        """Publish payload to canonical channel topic with QoS and optional ACK callback."""
        topic = self.build_topic(channel)
        return self.publish(topic, payload, qos=qos, retain=retain, on_ack=on_ack)

    def publish(
        self,
        topic: str,
        payload: str,
        qos: int = 1,
        retain: bool = False,
        on_ack: Optional[Callable[[], None]] = None,
    ) -> Tuple[bool, Optional[int]]:
        """Publish a message. Returns (success, message_id)."""
        if not self.is_connected() or not self._client:
            return False, None

        try:
            info = self._client.publish(topic, payload=payload, qos=qos, retain=retain)
            mid = info.mid
            with self._lock:
                self._last_published_at = time.time()
                if on_ack:
                    self._in_flight_acks[mid] = on_ack

            # For QoS 0, broker sends no PUBACK, invoke immediately
            if qos == 0 and on_ack:
                with self._lock:
                    self._in_flight_acks.pop(mid, None)
                    self._last_ack_at = time.time()
                on_ack()

            return True, mid
        except Exception as e:
            logger.error(f"Failed to publish to {topic}: {e}")
            return False, None

    def subscribe_channel(
        self,
        channel: str,
        callback: Callable[[str, bytes], None],
        qos: int = 1,
    ) -> None:
        """Subscribe to a canonical channel."""
        topic = self.build_topic(channel)
        self.subscribe(topic, callback, qos=qos)

    def subscribe(
        self,
        topic: str,
        callback: Callable[[str, bytes], None],
        qos: int = 1,
    ) -> None:
        """Subscribe to a raw topic pattern."""
        with self._lock:
            self._subscriptions[topic] = callback

        if self.is_connected() and self._client:
            try:
                self._client.subscribe(topic, qos=qos)
                logger.info(f"Subscribed to topic: {topic} (QoS: {qos})")
            except Exception as e:
                logger.error(f"Failed to subscribe to {topic}: {e}")

    # Callbacks
    def _on_connect(self, client, userdata, flags, rc, properties=None):
        rc_code = rc if isinstance(rc, int) else getattr(rc, "value", rc)
        if rc_code == 0:
            with self._lock:
                self._state = MQTTConnectionState.CONNECTED
                self._last_connected_at = time.time()
                self._current_retry_delay = self.initial_retry_delay
            logger.info(f"MQTT Connected successfully to {self.broker_host}:{self.broker_port}")

            # Re-subscribe to registered channels
            with self._lock:
                topics_to_sub = list(self._subscriptions.keys())
            for topic in topics_to_sub:
                client.subscribe(topic, qos=1)
        else:
            logger.error(f"MQTT Connection refused with return code: {rc_code}")
            with self._lock:
                self._state = MQTTConnectionState.ERROR
            self._schedule_reconnect()

    def _on_disconnect(self, client, userdata, disconnect_flags_or_rc, properties=None):
        with self._lock:
            was_connected = (self._state == MQTTConnectionState.CONNECTED)
            if self._running:
                self._state = MQTTConnectionState.RECONNECTING
            else:
                self._state = MQTTConnectionState.DISCONNECTED

        if was_connected:
            logger.warning("MQTT connection lost. Transitioning to RECONNECTING state.")
            self._schedule_reconnect()

    def _on_publish(self, client, userdata, mid, reason_codes=None, properties=None):
        """Called upon broker receipt of PUBACK for QoS 1 or PUBCOMP for QoS 2."""
        callback = None
        with self._lock:
            self._last_ack_at = time.time()
            callback = self._in_flight_acks.pop(mid, None)

        if callback:
            try:
                callback()
            except Exception as e:
                logger.error(f"Error in MQTT on_publish ACK callback for mid {mid}: {e}")

    def _on_message(self, client, userdata, message):
        topic = message.topic
        payload = message.payload
        logger.debug(f"Received MQTT message on topic: {topic}")

        callback = None
        with self._lock:
            for sub_topic, cb in self._subscriptions.items():
                if sub_topic == topic:
                    callback = cb
                    break

        if callback:
            try:
                callback(topic, payload)
            except Exception as e:
                logger.error(f"Error in subscription callback for {topic}: {e}")

    def _schedule_reconnect(self) -> None:
        """Launch reconnect thread with exponential backoff if not already running."""
        with self._lock:
            if not self._running:
                return
            if self._reconnect_thread and self._reconnect_thread.is_alive():
                return
            self._reconnect_thread = threading.Thread(
                target=self._reconnect_loop, name="MQTT-Reconnect", daemon=True
            )
            self._reconnect_thread.start()

    def _reconnect_loop(self) -> None:
        while self._running:
            with self._lock:
                if self._state == MQTTConnectionState.CONNECTED:
                    return
                delay = self._current_retry_delay
                # Exponential backoff with ceiling
                self._current_retry_delay = min(
                    self._current_retry_delay * 2.0, self.max_retry_delay
                )

            logger.info(f"Retrying MQTT connection in {delay:.1f}s...")
            time.sleep(delay)

            with self._lock:
                if not self._running:
                    return

            try:
                if self._client:
                    self._client.reconnect()
                    return
            except Exception as e:
                logger.debug(f"Reconnect attempt failed: {e}")
