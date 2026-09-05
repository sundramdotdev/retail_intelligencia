# MQTT Architecture & Topic Taxonomy

Retail Intelligencia utilizes Eclipse Mosquitto (MQTT v5.0 / v3.1.1) as the primary messaging backbone between Edge AI physical nodes and the FastAPI Device Gateway.

---

## 1. Topic Taxonomy

Every MQTT topic adheres to a strict canonical 5-segment hierarchy:

```text
retail / {environment} / {storeId} / {deviceId} / {channel}
```

### Path Segments

| Segment | Constraints | Description | Examples |
| :--- | :--- | :--- | :--- |
| `prefix` | Constant `retail` | System namespace root | `retail` |
| `environment` | `dev`, `staging`, `prod` | Multi-environment isolation | `dev`, `prod` |
| `storeId` | Alphanumeric string | Physical retail store identifier | `store_001`, `store_sf_04` |
| `deviceId` | Alphanumeric string | Unique hardware edge computing node | `edge-dev-001`, `edge_jetson_02` |
| `channel` | `events`, `heartbeat`, `telemetry`, `commands` | Dedicated data stream | `events`, `heartbeat` |

---

## 2. Channels and Payloads

### A. `events` Channel
* **Direction**: Edge → Gateway
* **QoS**: QoS 1 (At least once delivery)
* **Payload**: Single `RetailEvent` or JSON array of `RetailEvent` envelopes conforming to `schemaVersion: "1.0"`.
* **Broker Handling**: Forwarded directly to the FastAPI Gateway MQTT consumer and ingested into PostgreSQL via the TypeScript Data Service.

### B. `heartbeat` Channel
* **Direction**: Edge → Gateway
* **QoS**: QoS 1
* **Interval**: Every 15 seconds
* **Payload**:
```json
{
  "deviceId": "edge-dev-001",
  "storeId": "store_001",
  "timestamp": "2026-09-06T10:15:30Z",
  "status": "ONLINE",
  "firmwareVersion": "1.0.0"
}
```

### C. `telemetry` Channel
* **Direction**: Edge → Gateway
* **QoS**: QoS 0
* **Interval**: Every 60 seconds
* **Payload**: Includes CPU usage, GPU utilization, temperature, RAM consumption, inference FPS, and camera stream health.

---

## 3. Boundary & Tenant Enforcement

The FastAPI Gateway MQTT Consumer validates that the payload `storeId` and `deviceId` match the topic path segments:
```python
if evt.get("storeId") != topic_store_id or evt.get("deviceId") != topic_device_id:
    logger.error("Rejecting event: topic and payload storeId/deviceId mismatch")
    return
```
This guarantees physical hardware isolation across multi-tenant retail locations.
