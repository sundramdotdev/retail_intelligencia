# PostgreSQL Database Schema & Prisma ORM

The central database uses PostgreSQL 16 managed exclusively via Prisma ORM (`services/data/prisma/schema.prisma`).

---

## 1. Entity-Relationship Model

```text
  ┌──────────────┐
  │    Store     │
  └──────┬───────┘
         │ 1:N
         ├───► Device ───► Camera
         ├───► Zone
         ├───► Event (Unique eventId) ───► Alert (1:1)
         ├───► Task
         ├───► User (Staff / Manager)
         └───► Metric (Aggregations)
```

---

## 2. Core Tables

### 1. `stores`
Stores physical supermarket or retail locations.
* `storeId` (PK, text): e.g. `store_001`
* `name`, `city`, `state`, `country`, `timezone`
* `createdAt`, `updatedAt`

### 2. `devices`
Physical edge computing appliances.
* `deviceId` (PK, text): e.g. `edge-dev-001`
* `storeId` (FK → `stores.storeId`, CASCADE)
* `status` (`ONLINE`, `OFFLINE`, `DEGRADED`, `PROVISIONED`)
* `hardwareModel`, `macAddress`, `ipAddress`, `lastHeartbeatAt`

### 3. `cameras`
RTSP camera streams attached to an edge node.
* `cameraId` (PK, text): e.g. `cam-01`
* `deviceId` (FK → `devices.deviceId`, CASCADE)
* `rtspUrl`, `name`, `status`, `resolution`

### 4. `zones`
Physical zones projected from camera views into the store map.
* `zoneId` (PK, text): e.g. `zone-aisle-01`
* `storeId` (FK → `stores.storeId`, CASCADE)
* `name`, `type` (`QUEUE`, `SHELF`, `ENTRANCE`, `AISLE`, `CHECKOUT`)
* `polygon` (JSON): Coordinates array `[[x1,y1], [x2,y2], ...]`

### 5. `events`
Immutable record of every Canonical `RetailEvent` emitted by edge nodes.
* `eventId` (PK, text, unique ULID): e.g. `evt_01J...`
* `eventType` (text): `SHELF_LOW_STOCK`, `SHELF_EMPTY`, `QUEUE_HIGH`, `TRAFFIC_HIGH`, `TRAFFIC_LOW`, `ZONE_DWELL`, `DEVICE_HEALTH`
* `deviceId`, `storeId`, `zoneId`, `timestamp`, `confidence`, `severity`
* `metadata` (JSON), `source` (JSON)
* **Indexes**: `(storeId, timestamp)`, `(eventType, timestamp)`, `(zoneId, timestamp)`

### 6. `alerts`
Actionable conditions requiring human or automated notification.
* `alertId` (PK, text, unique)
* `eventId` (FK → `events.eventId`, unique)
* `status` (`ACTIVE`, `ACKNOWLEDGED`, `RESOLVED`, `EXPIRED`)
* `severity` (`INFO`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`)
* `acknowledgedBy`, `acknowledgedAt`, `message`

### 7. `tasks`
Staff dispatch tasks generated from alerts or managers.
* `taskId` (PK, text, unique)
* `storeId`, `zoneId`
* `type` (`RESTOCK_SHELF`, `OPEN_REGISTER`, `ASSIST_CUSTOMER`, `CLEAN_AISLE`, `INSPECT_DEVICE`)
* `priority` (`LOW`, `MEDIUM`, `HIGH`, `URGENT`)
* `status` (`DETECTED`, `ASSIGNED`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`)
* `assignedUserId`, `assignedAt`, `completedAt`, `resolutionNotes`

### 8. `users`
Store staff and platform administrators.
* `userId` (PK, text, unique)
* `email`, `role` (`PLATFORM_ADMIN`, `STORE_MANAGER`, `STORE_STAFF`, `READ_ONLY`)
* `storeId` (Nullable FK for multi-store admins)

### 9. `metrics`
Time-bucketed rollups for high-speed dashboard KPI charts.
* `metricId` (PK, text)
* `storeId`, `zoneId`, `metricName`, `timestamp`, `value`, `interval`
