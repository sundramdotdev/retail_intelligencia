# Backend Platform & Multi-Tier Architecture

Retail Intelligencia implements an enterprise, multi-tier data processing pipeline strictly respecting separation of concerns between device ingress, persistence, business logic, and human APIs.

---

## 1. System Topology

```text
┌────────────────────────────────┐
│      PHYSICAL EDGE NODES       │
│  (Camera → YOLO → EventBuffer) │
└───────────────┬────────────────┘
                │
                │ MQTT (TLS) / HTTPS Fallback
                ▼
┌────────────────────────────────┐
│    FASTAPI DEVICE GATEWAY      │
│  - Device Authentication       │
│  - Store Boundary Enforcement  │
│  - MQTT Background Ingestion   │
│  - Public REST API (/api/v1)   │
└───────────────┬────────────────┘
                │
                │ Internal HTTP Contract (X-Internal-Secret)
                ▼
┌────────────────────────────────┐
│    TYPESCRIPT DATA SERVICE     │
│  - Fastify High-Performance    │
│  - Atomic Event Deduplication  │
│  - Alert & Task Escalation     │
│  - Business Rule Engine        │
│  - Prisma Client ORM           │
└───────────────┬────────────────┘
                │
                │ Direct TCP Connection
                ▼
┌────────────────────────────────┐
│      POSTGRESQL 16 DATABASE    │
│  - Normalized Relational Model │
│  - Timescale/B-Tree Indexes    │
│  - Foreign Key Constraints     │
└────────────────────────────────┘
```

---

## 2. Invariant: Strict Service Boundaries

1. **FastAPI Gateway Boundary**:
   - Python code NEVER imports Prisma or attempts direct SQL queries to PostgreSQL.
   - FastAPI is stateless and communicates with the data layer strictly via the internal HTTP service contract.
   - FastAPI enforces rate limits, token authentication, and multi-tenant store boundary isolation.

2. **TypeScript Data Service Boundary**:
   - Sole custodian of the PostgreSQL database connection and Prisma schema migrations.
   - Processes internal event batches idempotently based on unique `eventId`.
   - Computes alert escalation rules and coordinates staff task assignment workflows.
   - Fully isolated behind an internal subnet, rejecting any traffic lacking `X-Internal-Secret`.

3. **PostgreSQL Database Boundary**:
   - Exclusively managed by Prisma schema migrations.
   - Foreign key cascades ensure consistent teardown of devices, cameras, zones, events, and metrics when stores or parent entities are decommissioned.
