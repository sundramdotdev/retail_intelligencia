# Edge Device Provisioning & Registration Protocol

This document outlines the enrollment lifecycle for Retail Intelligencia physical edge nodes.

---

## 1. Enrollment Overview

Edge AI nodes are provisioned in retail stores with a hardware-bound provisioning key. Before an edge node can publish events over MQTT or access central store configuration, it must complete the registration handshake.

```text
┌────────────────┐                     ┌─────────────────────┐                     ┌───────────────────────┐
│ Edge Hardware  │                     │   FastAPI Gateway   │                     │ TypeScript Data Svc   │
└───────┬────────┘                     └──────────┬──────────┘                     └───────────┬───────────┘
        │                                         │                                            │
        │ 1. POST /api/v1/devices/register        │                                            │
        │    { deviceId, storeId, provKey, ... }  │                                            │
        │ ───────────────────────────────────────>│                                            │
        │                                         │ 2. POST /internal/devices/register         │
        │                                         │ ──────────────────────────────────────────>│
        │                                         │                                            │ 3. Create or update
        │                                         │                                            │    Device record
        │                                         │ 4. 200 OK (Device record)                  │    (status: PROVISIONED)
        │                                         │ <──────────────────────────────────────────│
        │ 5. 200 OK { deviceToken, mqttBrokerUrl }│                                            │
        │ <───────────────────────────────────────│                                            │
        │                                         │                                            │
        │ 6. Connect MQTT (TLS)                   │                                            │
        │ ───────────────────────────────────────>│                                            │
        │ 7. Begin Heartbeat (every 15s)          │                                            │
        │ ───────────────────────────────────────>│                                            │
```

---

## 2. Registration API Schema

### Request
`POST /api/v1/devices/register`

```json
{
  "deviceId": "edge-dev-001",
  "storeId": "store_001",
  "hardwareModel": "Jetson-Orin-Nano-8GB",
  "macAddress": "70:B3:D5:E2:81:4A",
  "ipAddress": "192.168.1.120",
  "capabilities": {
    "tensorrt": true,
    "cudaVersion": "12.2",
    "accelerator": "NVIDIA Orin",
    "camerasSupported": 4
  },
  "provisioningKey": "demo_provisioning_key_2026"
}
```

### Response
`200 OK`

```json
{
  "deviceId": "edge-dev-001",
  "storeId": "store_001",
  "status": "PROVISIONED",
  "mqttBrokerUrl": "tls://localhost:8883",
  "deviceToken": "devkey_edge-dev-001_secret"
}
```

---

## 3. Local Credential Persistence

Upon receiving credentials:
1. The edge node encrypts and persists `deviceToken` and `mqttBrokerUrl` in `/etc/retail-intelligencia/device.conf` (or local secure store).
2. The registration client sets `is_registered = True`.
3. The background heartbeat daemon initializes and announces liveness.
