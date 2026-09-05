# Offline-First Resilience & Edge Buffering

In physical retail environments, local Wi-Fi or backhaul WAN connections frequently experience degradation, interference, or outright drops. Retail Intelligencia is designed from the ground up to **never stop detecting or drop events** during network partitions.

---

## 1. Edge Storage Architecture

The edge device maintains an embedded SQLite database configured with **Write-Ahead Logging (WAL)**:

```text
┌─────────────────────────────────────────────────────────────┐
│                    EDGE COMPUTING NODE                      │
│                                                             │
│   YOLO Detection / ByteTrack / Zone Rules                   │
│                       │                                     │
│                       ▼                                     │
│             RetailEvent Generation                          │
│                       │                                     │
│                       ▼                                     │
│          DurableOfflineQueue (SQLite WAL)                   │
│          ┌───────────────────────────────────┐              │
│          │  - FIFO ordering                  │              │
│          │  - Max Capacity: 10,000 events    │              │
│          │  - Max Disk Footprint: 100 MB     │              │
│          │  - Oldest-first FIFO eviction     │              │
│          └───────────────────────────────────┘              │
│                       │                                     │
│                       ▼ (Poll & Drain)                      │
│                EventDispatcher                              │
│                       │                                     │
│       ┌───────────────┴───────────────┐                     │
│       ▼                               ▼                     │
│  [Network Offline]            [Network Online]              │
│  Events stay buffered          Replay with Rate Limit       │
│  Zero data loss                (50 events / sec)            │
└───────────────────────────────────────┬─────────────────────┘
                                        ▼ (MQTT QoS 1 / HTTPS)
                              FastAPI Device Gateway
```

---

## 2. Retention & Eviction Policy

| Parameter | Configuration | Behavior |
| :--- | :--- | :--- |
| **Storage Engine** | SQLite 3 (`WAL` mode) | Non-blocking concurrent writes from inference thread |
| **Max Pending Items** | 10,000 events | Bounded memory and disk consumption |
| **Max DB File Size** | 100 MB | Safeguards physical flash storage from wear & exhaustion |
| **Eviction Strategy** | Oldest-first FIFO | If disk or item limit is breached, oldest acknowledged or low-severity events are purged |
| **State Machine** | `PENDING → PUBLISHING → ACKNOWLEDGED / FAILED` | Strict lifecycle tracking |

---

## 3. Reconnection & Auto-Replay Engine

When the network is restored:
1. `EdgeMQTTClient` establishes connection with automatic exponential backoff (1s, 2s, 4s ... max 60s).
2. The `EventDispatcher` detects connection status and begins reading `PENDING` events in batches of 50.
3. Events are published with rate-limiting (default 50 eps) to prevent thundering herd overload on the central gateway.
4. Each batch receives an explicit message ACK before being marked `ACKNOWLEDGED` in the local queue.
5. In the event of an abrupt disconnect mid-flight, unacknowledged events remain `PENDING` and are safely retransmitted upon the next reconnection.
6. The backend's atomic `eventId` deduplication guarantees zero duplicate records in PostgreSQL.
