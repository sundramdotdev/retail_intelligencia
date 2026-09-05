# docs/database/entities.md — Database Entities Specification

> **RELATIONAL DATA DICTIONARY (PRISMA / POSTGRESQL)**
> 
> This document specifies the 8 core relational entities for Retail Intelligencia. All models are managed via Prisma ORM by the Node.js/TypeScript Data Service.

---

## 1. Entity Overview

The system models the retail domain across 8 primary entities:

1. **`Store`**: Physical store facility, location metadata, timezone, and operating parameters.
2. **`Device`**: Physical edge AI appliance deployed inside a specific store.
3. **`Camera`**: Optical sensor connected to a device covering store areas.
4. **`Zone`**: Calibrated 2D polygon floor zone mapped to operational retail functions.
5. **`Event`**: Immutable persistence record of a canonical `RetailEvent` envelope.
6. **`Alert`**: Deduplicated operational condition requiring immediate attention.
7. **`Task`**: Actionable work item assigned to retail floor staff.
8. **`User`**: Human user account (Store Manager, Staff, Platform Admin).

---

## 2. Detailed Entity Data Dictionary

### 2.1 Entity: `Store`
* **Purpose**: Represents a distinct physical supermarket or retail branch.
* **Fields**:
  * `id`: `String` (UUID / ULID), Primary Key.
  * `storeCode`: `String`, Unique (e.g., `"store_001"`).
  * `name`: `String` (e.g., `"Market Street Superstore"`).
  * `address`: `String`.
  * `city`: `String`.
  * `state`: `String`.
  * `postalCode`: `String`.
  * `country`: `String` (ISO 3166-1 alpha-2, e.g. `"US"`).
  * `timezone`: `String` (IANA Timezone, e.g. `"America/Los_Angeles"`).
  * `operatingHours`: `Json` (Opening/closing schedules per day of week).
  * `createdAt`: `DateTime`, Default: `now()`.
  * `updatedAt`: `DateTime`, Auto-updated.

---

### 2.2 Entity: `Device`
* **Purpose**: Represents a physical edge computing node deployed in a store.
* **Fields**:
  * `id`: `String`, Primary Key.
  * `deviceId`: `String`, Unique (e.g., `"edge_001"`).
  * `storeId`: `String`, Foreign Key ──► `Store.id` (ON DELETE RESTRICT).
  * `hardwareModel`: `String` (e.g., `"Jetson-Orin-NX-16GB"`).
  * `macAddress`: `String`, Unique.
  * `status`: `Enum` (`UNPROVISIONED`, `PROVISIONED`, `ONLINE`, `DEGRADED`, `OFFLINE`).
  * `firmwareVersion`: `String`.
  * `runtimeVersion`: `String`.
  * `lastHeartbeatAt`: `DateTime`, Nullable.
  * `certificateThumbprint`: `String`, Nullable.
  * `createdAt`: `DateTime`, Default: `now()`.
  * `updatedAt`: `DateTime`, Auto-updated.

---

### 2.3 Entity: `Camera`
* **Purpose**: Represents an optical video sensor managed by an edge appliance.
* **Fields**:
  * `id`: `String`, Primary Key.
  * `cameraId`: `String` (e.g., `"cam_aisle_04"`).
  * `deviceId`: `String`, Foreign Key ──► `Device.id` (ON DELETE CASCADE).
  * `storeId`: `String`, Foreign Key ──► `Store.id`.
  * `streamType`: `Enum` (`RTSP`, `USB_V4L2`).
  * `streamUrl`: `String` (Encrypted / stored locally).
  * `resolutionWidth`: `Int` (e.g., `1920`).
  * `resolutionHeight`: `Int` (e.g., `1080`).
  * `configuredFps`: `Int` (e.g., `15`).
  * `mountLocation`: `String` (e.g., `"Ceiling Bay 4"`).
  * `status`: `Enum` (`ONLINE`, `DEGRADED`, `OFFLINE`).
  * `createdAt`: `DateTime`, Default: `now()`.

---

### 2.4 Entity: `Zone`
* **Purpose**: Represents a defined physical polygon within a camera's field of view.
* **Fields**:
  * `id`: `String`, Primary Key.
  * `zoneCode`: `String` (e.g., `"zone_checkout_02"`).
  * `storeId`: `String`, Foreign Key ──► `Store.id` (ON DELETE CASCADE).
  * `cameraId`: `String`, Foreign Key ──► `Camera.id` (ON DELETE CASCADE).
  * `name`: `String` (e.g., `"Checkout Lane 2 Queue"`).
  * `zoneType`: `Enum` (`QUEUE`, `SHELF`, `TRAFFIC_AISLE`, `DWELL_AREA`, `ENTRANCE`).
  * `polygonCoordinates`: `Json` (Array of `[x, y]` normalized or pixel vertices).
  * `thresholds`: `Json` (e.g., `{"queueLimit": 6, "durationSeconds": 60}`).
  * `isActive`: `Boolean`, Default: `true`.
  * `createdAt`: `DateTime`, Default: `now()`.

---

### 2.5 Entity: `Event`
* **Purpose**: Immutable persistence of the canonical `RetailEvent` envelope.
* **Fields**:
  * `id`: `String`, Primary Key.
  * `eventId`: `String`, Unique (The canonical ULID from edge, e.g. `"evt_01J98..."`).
  * `eventVersion`: `String` (e.g., `"1.0"`).
  * `eventType`: `Enum` (`SHELF_LOW_STOCK`, `SHELF_EMPTY`, `QUEUE_HIGH`, `TRAFFIC_HIGH`, `TRAFFIC_LOW`, `ZONE_DWELL`, `DEVICE_HEALTH`).
  * `deviceId`: `String`, Foreign Key ──► `Device.deviceId`.
  * `storeId`: `String`, Foreign Key ──► `Store.storeCode`.
  * `zoneId`: `String`, Foreign Key ──► `Zone.zoneCode`, Nullable.
  * `timestamp`: `DateTime` (UTC timestamp from edge).
  * `confidence`: `Float`.
  * `severity`: `Enum` (`INFO`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
  * `metadata`: `Json` (Structured event-specific payload).
  * `source`: `Json` (`cameraId`, `modelId`, `modelVersion`).
  * `schemaVersion`: `String`, Default: `"1.0"`.
  * `receivedAt`: `DateTime`, Default: `now()`.

---

### 2.6 Entity: `Alert`
* **Purpose**: Actionable operational problem generated from one or more events.
* **Fields**:
  * `id`: `String`, Primary Key.
  * `alertCode`: `String`, Unique (e.g., `"alt_01J98..."`).
  * `eventId`: `String`, Foreign Key ──► `Event.eventId`.
  * `storeId`: `String`, Foreign Key ──► `Store.storeCode`.
  * `zoneId`: `String`, Foreign Key ──► `Zone.zoneCode`, Nullable.
  * `alertType`: `String`.
  * `severity`: `Enum` (`INFO`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
  * `status`: `Enum` (`ACTIVE`, `ACKNOWLEDGED`, `RESOLVED`, `EXPIRED`).
  * `title`: `String`.
  * `message`: `String`.
  * `acknowledgedByUserId`: `String`, Foreign Key ──► `User.id`, Nullable.
  * `acknowledgedAt`: `DateTime`, Nullable.
  * `resolvedAt`: `DateTime`, Nullable.
  * `createdAt`: `DateTime`, Default: `now()`.

---

### 2.7 Entity: `Task`
* **Purpose**: Actionable work item assigned to store personnel for physical resolution.
* **Fields**:
  * `id`: `String`, Primary Key.
  * `taskCode`: `String`, Unique (e.g., `"tsk_01J98..."`).
  * `storeId`: `String`, Foreign Key ──► `Store.storeCode`.
  * `zoneId`: `String`, Foreign Key ──► `Zone.zoneCode`, Nullable.
  * `alertId`: `String`, Foreign Key ──► `Alert.id`, Nullable.
  * `title`: `String` (e.g., `"Restock Beverage Shelf Aisle 4"`).
  * `description`: `String`.
  * `priority`: `Enum` (`LOW`, `MEDIUM`, `HIGH`, `URGENT`).
  * `status`: `Enum` (`DETECTED`, `ASSIGNED`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`).
  * `assignedToUserId`: `String`, Foreign Key ──► `User.id`, Nullable.
  * `assignedAt`: `DateTime`, Nullable.
  * `completedAt`: `DateTime`, Nullable.
  * `resolutionNotes`: `String`, Nullable.
  * `createdAt`: `DateTime`, Default: `now()`.
  * `updatedAt`: `DateTime`, Auto-updated.

---

### 2.8 Entity: `User`
* **Purpose**: Authenticated human operator or manager.
* **Fields**:
  * `id`: `String`, Primary Key.
  * `email`: `String`, Unique.
  * `passwordHash`: `String`.
  * `fullName`: `String`.
  * `role`: `Enum` (`PLATFORM_ADMIN`, `STORE_MANAGER`, `STORE_STAFF`).
  * `storeId`: `String`, Foreign Key ──► `Store.storeCode`, Nullable (Null for Platform Admin).
  * `isActive`: `Boolean`, Default: `true`.
  * `lastLoginAt`: `DateTime`, Nullable.
  * `createdAt`: `DateTime`, Default: `now()`.
