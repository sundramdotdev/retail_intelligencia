# TypeScript Data Service & Internal Contract

The TypeScript Data Service (`services/data`) is the high-performance core responsible for data persistence, schema governance, atomic event deduplication, and business rule evaluation.

---

## 1. Internal HTTP Contract

The Data Service listens on port `5000` and exposes internal endpoints accessible solely to the FastAPI Gateway via `X-Internal-Secret`:

| Method | Internal Endpoint | Purpose |
| :--- | :--- | :--- |
| `POST` | `/internal/events` | Ingest batch of events, deduplicate on `eventId`, trigger alert escalation |
| `GET` | `/internal/events` | Query stored events by store, zone, and time range |
| `GET` | `/internal/events/:id` | Fetch unique event envelope |
| `POST` | `/internal/devices/register` | Register or update edge device |
| `GET` | `/internal/devices/:id` | Retrieve device record |
| `POST` | `/internal/devices/:id/heartbeat` | Update device last heartbeat timestamp |
| `GET` | `/internal/stores` | List all stores |
| `GET` | `/internal/stores/:id` | Get single store |
| `GET` | `/internal/stores/:id/zones` | Get physical zones configured for store |
| `GET` | `/internal/alerts` | Query active/acknowledged alerts |
| `POST` | `/internal/alerts/:id/acknowledge` | Mark alert as acknowledged by user |
| `GET` | `/internal/tasks` | Query tasks |
| `POST` | `/internal/tasks` | Create task |
| `POST` | `/internal/tasks/:id/assign` | Assign task to store associate |
| `POST` | `/internal/tasks/:id/complete` | Complete task with notes |
| `GET` | `/internal/analytics/overview` | Store KPI aggregations |

---

## 2. Atomic Event Deduplication

To handle edge network retransmissions and replay bursts safely:
1. Every event has a unique ULID `eventId` (`evt_...`).
2. The `event.repository.ts` attempts an idempotent lookup or atomic upsert on `eventId`.
3. If an event already exists, it is marked as duplicate and skipped.
4. Alerts and staff tasks are only evaluated for novel, accepted events.

---

## 3. Alert Escalation & Cooldown Hysteresis

The Data Service includes `escalation.ts` which converts critical events into operational alerts:
* `SHELF_EMPTY` or `SHELF_LOW_STOCK` triggers a restock alert and automatically generates a high-priority staff task.
* `QUEUE_HIGH` triggers a register congestion alert and generates a cashier dispatch task.
* **Cooldown Hysteresis**: Prevents alert storms by enforcing a minimum 5-minute cooldown per zone before generating duplicate alerts of the same type.
