"""Background MQTT Consumer for Retail Intelligencia.

Subscribes to canonical MQTT topics:
  retail/{env}/+/+/events
  retail/{env}/+/+/heartbeat
  retail/{env}/+/+/telemetry

Validates message envelope, topic-payload consistency, and forwards
to the TypeScript Data Service via internal HTTP contract.

After ingestion, broadcasts SSE events to connected dashboard clients:
  - EVENT_RECEIVED   : every validated retail event
  - ALERT_TRIGGERED  : when the escalation engine creates a new alert
  - TASK_CREATED     : when the escalation engine creates a new task
  - DEVICE_STATUS    : on heartbeat updates
"""
import asyncio
import json
import logging
from typing import List, Optional
import paho.mqtt.client as mqtt

from app.core.config import settings
from app.clients.data_service import data_client
from app.models.retail_event import CanonicalRetailEvent
from app.realtime.metrics_store import live_metrics_store

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
            client.subscribe(f"retail/{settings.environment}/+/+/metrics", qos=0)
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
                    # Fire async coroutine: ingest events, then broadcast SSE
                    asyncio.run_coroutine_threadsafe(
                        self._ingest_and_broadcast(valid_events, topic_store_id),
                        self._loop,
                    )

            elif channel == "heartbeat":
                ts = payload.get("timestamp")
                device_id = payload.get("deviceId", topic_device_id)
                if ts and self._loop and not self._loop.is_closed():
                    asyncio.run_coroutine_threadsafe(
                        self._handle_heartbeat(topic_device_id, ts, topic_store_id),
                        self._loop,
                    )

            elif channel == "telemetry":
                # Forward device health telemetry as SSE DEVICE_STATUS
                if self._loop and not self._loop.is_closed():
                    from app.realtime.broadcaster import broadcaster
                    broadcaster.broadcast_sync(
                        store_id=topic_store_id,
                        event_type="DEVICE_STATUS",
                        data={
                            "deviceId": topic_device_id,
                            "storeId": topic_store_id,
                            **payload,
                        },
                    )

            elif channel == "metrics":
                # Update in-memory live metrics store
                live_metrics_store.update(topic_store_id, topic_device_id, payload)
                
                # Broadcast LIVE_METRICS via SSE
                if self._loop and not self._loop.is_closed():
                    from app.realtime.broadcaster import broadcaster
                    metrics_summary = live_metrics_store.get_for_device(topic_device_id)
                    if metrics_summary:
                        broadcaster.broadcast_sync(
                            store_id=topic_store_id,
                            event_type="LIVE_METRICS",
                            data=metrics_summary,
                        )
                        # Also forward to ZONE_TELEMETRY if zone occupancy is present
                        zone_occ = metrics_summary.get("zoneOccupancy")
                        if zone_occ:
                            broadcaster.broadcast_sync(
                                store_id=topic_store_id,
                                event_type="ZONE_TELEMETRY",
                                data={"storeId": topic_store_id, "deviceId": topic_device_id, "occupancy": zone_occ},
                            )

        except Exception as e:
            logger.error(f"Error processing MQTT message on topic {msg.topic}: {e}", exc_info=True)

    async def _ingest_and_broadcast(self, valid_events: List[dict], store_id: str) -> None:
        """Ingest events into the Data Service, then broadcast SSE events.

        Flow:
          EVENT_RECEIVED  → broadcast each validated event immediately
          ALERT_TRIGGERED → broadcast using inline escalation data from Data Service
          TASK_UPDATED    → broadcast using inline task data from Data Service
        """
        from app.realtime.broadcaster import broadcaster

        # 1. Broadcast EVENT_RECEIVED immediately for every validated event
        for evt in valid_events:
            await broadcaster.broadcast(
                store_id=store_id,
                event_type="EVENT_RECEIVED",
                data=evt,
            )
            logger.info(
                f"[SSE] EVENT_RECEIVED: {evt.get('eventType')} "
                f"eventId={evt.get('eventId')} zone={evt.get('zoneId')}"
            )

        # 2. Forward to Data Service (idempotent insertion + escalation)
        try:
            result = await data_client.ingest_events(valid_events)
            accepted = result.get("acceptedCount", 0)
            duplicates = result.get("duplicateCount", 0)
            logger.info(f"Data Service: accepted={accepted} duplicates={duplicates}")

            # 3. Broadcast ALERT_TRIGGERED and TASK_UPDATED from inline escalation results
            for escalation in result.get("escalations", []):
                alert = escalation.get("alert")
                task = escalation.get("task")

                if alert:
                    await broadcaster.broadcast(
                        store_id=store_id,
                        event_type="ALERT_TRIGGERED",
                        data=alert,
                    )
                    logger.info(
                        f"[SSE] ALERT_TRIGGERED: {alert.get('alertType')} "
                        f"alertCode={alert.get('alertCode')} severity={alert.get('severity')}"
                    )

                if task:
                    await broadcaster.broadcast(
                        store_id=store_id,
                        event_type="TASK_UPDATED",
                        data={**task, "action": "CREATED"},
                    )
                    logger.info(
                        f"[SSE] TASK_UPDATED (CREATED): {task.get('title')} "
                        f"taskCode={task.get('taskCode')} priority={task.get('priority')}"
                    )

        except Exception as e:
            logger.error(f"Error during ingest_and_broadcast: {e}", exc_info=True)

    async def _handle_heartbeat(self, device_id: str, timestamp: str, store_id: str) -> None:
        """Process device heartbeat and broadcast DEVICE_STATUS over SSE."""
        from app.realtime.broadcaster import broadcaster
        await data_client.update_device_heartbeat(device_id, timestamp)
        await broadcaster.broadcast(
            store_id=store_id,
            event_type="DEVICE_STATUS",
            data={
                "deviceId": device_id,
                "storeId": store_id,
                "lastHeartbeatAt": timestamp,
                "status": "ONLINE",
            },
        )

    def start(self, loop: asyncio.AbstractEventLoop):
        if not settings.mqtt_enabled:
            logger.info("MQTT Consumer is disabled in settings.")
            return

        self._loop = loop
        try:
            self.client = mqtt.Client(
                client_id=f"{settings.mqtt_client_id}-sub",
                protocol=mqtt.MQTTv311,
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
