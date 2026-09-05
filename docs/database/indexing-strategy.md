# docs/database/indexing-strategy.md — Indexing Strategy Specification

> **DATABASE INDEXING & HIGH-VELOCITY QUERY OPTIMIZATION**
> 
> This document specifies the indexing strategy across all relational tables in PostgreSQL, ensuring sub-10ms response times for operational dashboards and high-throughput ingestion of edge telemetry.

---

## 1. Primary Indexes & Constraints

| Table | Index Column(s) | Index Type | Constraint / Purpose |
| :--- | :--- | :---: | :--- |
| **`Store`** | `id` | B-tree | Primary Key |
| **`Store`** | `storeCode` | B-tree | Unique (Business Key) |
| **`Device`** | `id` | B-tree | Primary Key |
| **`Device`** | `deviceId` | B-tree | Unique (Hardware Key) |
| **`Device`** | `macAddress` | B-tree | Unique |
| **`Camera`** | `id` | B-tree | Primary Key |
| **`Camera`** | `(deviceId, cameraId)` | B-tree | Unique |
| **`Zone`** | `id` | B-tree | Primary Key |
| **`Zone`** | `(storeId, zoneCode)` | B-tree | Unique |
| **`Event`** | `(id, timestamp)` | B-tree | Composite Primary Key (Partitioned) |
| **`Event`** | `eventId` | B-tree | Unique (Global Deduplication Key) |
| **`Alert`** | `id` | B-tree | Primary Key |
| **`Alert`** | `alertCode` | B-tree | Unique |
| **`Task`** | `id` | B-tree | Primary Key |
| **`Task`** | `taskCode` | B-tree | Unique |
| **`User`** | `id` | B-tree | Primary Key |
| **`User`** | `email` | B-tree | Unique (Login identifier) |

---

## 2. Composite Indexes for Common Query Patterns

Operational dashboards query data using predictable, store-scoped access patterns. The following composite indexes prevent full-table scans:

### 2.1 Event Query Patterns
* **Dashboard Recent Events Feed**:
  * Query: `WHERE store_id = $1 ORDER BY timestamp DESC LIMIT 50`
  * **Index**: `CREATE INDEX idx_event_store_timestamp ON "Event" (store_id, timestamp DESC);`
* **Zone-Specific Historical Drilldown**:
  * Query: `WHERE store_id = $1 AND zone_id = $2 AND timestamp BETWEEN $3 AND $4`
  * **Index**: `CREATE INDEX idx_event_store_zone_timestamp ON "Event" (store_id, zone_id, timestamp DESC);`
* **Event Type Filtering (e.g. all Queue events)**:
  * Query: `WHERE store_id = $1 AND event_type = $2 AND timestamp >= $3`
  * **Index**: `CREATE INDEX idx_event_store_type_timestamp ON "Event" (store_id, event_type, timestamp DESC);`

### 2.2 Alert & Task Operational Triage
* **Active Unresolved Alerts**:
  * Query: `WHERE store_id = $1 AND status = 'ACTIVE' ORDER BY created_at DESC`
  * **Index**: `CREATE INDEX idx_alert_store_status_created ON "Alert" (store_id, status, created_at DESC);`
* **Staff Member Task List**:
  * Query: `WHERE store_id = $1 AND assigned_to_user_id = $2 AND status IN ('ASSIGNED', 'IN_PROGRESS')`
  * **Index**: `CREATE INDEX idx_task_staff_status ON "Task" (store_id, assigned_to_user_id, status);`

---

## 3. Time-Series Optimization: BRIN vs B-Tree

For large partitioned historical tables, standard B-tree indexes can consume significant RAM:
* On the partitioned `Event` table, **BRIN (Block Range Index)** is used on historical partitions older than 14 days:
  ```sql
  CREATE INDEX idx_event_timestamp_brin ON "Event" USING BRIN (timestamp) WITH (pages_per_range = 128);
  ```
* **Benefit**: BRIN indexes are approximately 95% smaller than standard B-tree indexes, allowing months of historical time-series data to remain in memory cache while supporting high-speed range queries (`BETWEEN $start AND $end`).
