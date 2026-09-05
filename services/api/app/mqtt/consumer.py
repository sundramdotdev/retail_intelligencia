"""Background MQTT Consumer for Retail Intelligencia.

Subscribes to canonical MQTT topics:
  retail/{env}/+/+/events
  retail/{env}/+/+/heartbeat
  retail/{env}/+/+/telemetry

Validates message envelope, topic-payload consistency, and forwards
to the TypeScript Data Service via internal HTTP contract.
"""
import asyncio
import json
import logging
from typing import Optional
import paho.mqtt.client as mqtt

from app.core.config import settings
from app.clients.data_service import data_client
from app.models.retail_event import CanonicalRetailEvent

logger = logging.getLogger("api.mqtt_consumer")


class GatewayMqttConsumer:
    def __init__(self):
        self.client: Optional[mqtt.Client] = None
        self.is_connected: bool = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self.topic_filter = f"retail/{settings.environment}/+/+/+"

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        if rc == 0:
            self.is_connected = True
            logger.info(f"MQTT Consumer connected to {settings.mqtt_host}:{settings.mqtt_port}")
            # Subscribe to all events, heartbeats, and telemetry under environment
            client.subscribe(f"retail/{settings.environment}/+/+/events", qos=1)
            client.subscribe(f"retail/{settings.environment}/+/+/heartbeat", qos=1)
            client.subscribe(f"retail/{settings.environment}/+/+/telemetry", qos=1)
            logger.info(f"Subscribed to topics for environment: {settings.environment}")
        else:
            self.is_connected = False
            logger.warning(f"MQTT Consumer failed to connect, return code: {rc}")

    def _on_disconnect(self, client, userdata, rc, properties=None):
        self.is_connected = False
        logger.info(f"MQTT Consumer disconnected (rc={rc})")

    def _on_message(self, client, userdata, msg):
        try:
            topic_parts = msg.topic.split("/")
            # Topic format: retail/{env}/{storeId}/{deviceId}/{channel}
            if len(topic_parts) != 5:
                logger.warning(f"Rejecting malformed topic: {msg.topic}")
                return

            prefix, env, topic_store_id, topic_device_id, channel = topic_parts
            if prefix != "retail" or env != settings.environment:
                logger.warning(f"Ignoring topic from foreign environment/namespace: {msg.topic}")
                return

            payload_raw = msg.payload.decode("utf-8")
            payload = json.loads(payload_raw)

            if channel == "events":
                # Single or batch of events
                events_to_process = payload if isinstance(payload, list) else [payload]
                valid_events = []
                for evt in events_to_process:
                    # Enforce topic storeId/deviceId match payload
                    if evt.get("storeId") != topic_store_id or evt.get("deviceId") != topic_device_id:
                        logger.error(
                            f"Topic / payload boundary mismatch! Topic: ({topic_store_id}, {topic_device_id}) vs "
                            f"Payload: ({evt.get('storeId')}, {evt.get('deviceId')})"
                        )
                        continue

                    # Validate canonical model
                    try:
                        parsed = CanonicalRetailEvent(**evt)
                        valid_events.append(parsed.model_dump())
                    except Exception as val_err:
                        logger.warning(f"Rejecting invalid event {evt.get('eventId')}: {val_err}")

                if valid_events and self._loop and not self._loop.is_closed():
                    asyncio.run_coroutine_threadsafe(
                        data_client.ingest_events(valid_events),
                        self._loop,
                    )
                    # Broadcast to connected SSE dashboard clients
                    from app.realtime.broadcaster import broadcaster
                    for evt in valid_events:
                        broadcaster.broadcast_sync(
                            store_id=topic_store_id,
                            event_type="EVENT_RECEIVED",
                            data=evt,
                        )

            elif channel == "heartbeat":
                ts = payload.get("timestamp")
                if ts and self._loop and not self._loop.is_closed():
                    asyncio.run_coroutine_threadsafe(
                        data_client.update_device_heartbeat(topic_device_id, ts),
                        self._loop,
                    )

            elif channel == "telemetry":
                # Telemetry processing
                logger.debug(f"Received telemetry from device {topic_device_id}: {payload}")

        except Exception as e:
            logger.error(f"Error processing MQTT message on topic {msg.topic}: {e}", exc_info=True)

    def start(self, loop: asyncio.AbstractEventLoop):
        if not settings.mqtt_enabled:
            logger.info("MQTT Consumer is disabled in settings.")
            return

        self._loop = loop
        try:
            self.client = mqtt.Client(
                client_id=f"{settings.mqtt_client_id}-sub",
                protocol=mqtt.MQTTv5,
            )
            if settings.mqtt_username and settings.mqtt_password:
                self.client.username_pw_set(settings.mqtt_username, settings.mqtt_password)

            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message

            # Connect non-blocking
            self.client.connect_async(settings.mqtt_host, settings.mqtt_port, keepalive=60)
            self.client.loop_start()
            logger.info(f"MQTT Consumer loop started target {settings.mqtt_host}:{settings.mqtt_port}")
        except Exception as e:
            logger.warning(f"Could not initialize MQTT consumer (is broker running?): {e}")

    def stop(self):
        if self.client:
            try:
                self.client.loop_stop()
                self.client.disconnect()
            except Exception:
                pass
            self.is_connected = False
            logger.info("MQTT Consumer stopped.")


mqtt_consumer = GatewayMqttConsumer()
