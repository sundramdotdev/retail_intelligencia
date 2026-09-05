# FastAPI Device Gateway & Ingress API

The FastAPI Device Gateway sits at the frontline of edge communication, exposing both an internal MQTT consumer and a secure RESTful API.

---

## 1. REST Endpoints Overview

All routes are versioned under `/api/v1`:

### A. Health & Readiness
* `GET /health`: Overall gateway liveness and MQTT consumer connection status.
* `GET /ready`: Upstream Data Service reachability.

### B. Events Ingestion & Query
* `POST /api/v1/events`: Ingests single or batch `CanonicalRetailEvent` objects. Requires `Bearer devkey_*` and validates `storeId` & `deviceId` match device registration.
* `GET /api/v1/events?storeId={id}`: Queries historical events for a store (requires human user auth).
* `GET /api/v1/events/{eventId}`: Fetches a single event envelope.

### C. Devices
* `POST /api/v1/devices/register`: Enrolls an edge appliance with provisioning key validation.
* `GET /api/v1/devices/{deviceId}`: Retrieves hardware metadata and zone assignments.
* `GET /api/v1/devices/{deviceId}/health`: Edge device connectivity and telemetry.
* `POST /api/v1/devices/{deviceId}/heartbeat`: Direct HTTP heartbeat fallback.

### D. Stores & Zones
* `GET /api/v1/stores`: Lists retail locations accessible to the authenticated user.
* `GET /api/v1/stores/{storeId}`: Store metadata and counts.
* `GET /api/v1/stores/{storeId}/zones`: Physical polygon coordinates and zone types (`QUEUE`, `SHELF`, `AISLE`).

### E. Operational Alerts & Tasks
* `GET /api/v1/alerts?storeId={id}`: Active retail alerts.
* `POST /api/v1/alerts/{alertId}/acknowledge`: Acknowledges an alert by staff.
* `GET /api/v1/tasks?storeId={id}`: Actionable staff tasks.
* `POST /api/v1/tasks`: Task creation.
* `POST /api/v1/tasks/{taskId}/assign`: Assigns task to staff member.
* `POST /api/v1/tasks/{taskId}/complete`: Records completion with resolution notes.

### F. Analytics
* `GET /api/v1/analytics/overview?storeId={id}`: Store KPI cards.
* `GET /api/v1/analytics/traffic?storeId={id}&interval={hour|day|week}`: Foot traffic series.
* `GET /api/v1/analytics/queues?storeId={id}`: Checkout queue metrics.
* `GET /api/v1/analytics/dwell?storeId={id}`: Zone dwell time analysis.
* `GET /api/v1/analytics/shelves?storeId={id}`: Stock availability & out-of-stock count.

---

## 2. Store Boundary Protection Mechanism

```python
for evt in events:
    if evt.storeId != device.store_id:
        raise HTTPException(
            status_code=403,
            detail={"error": {"code": "STORE_MISMATCH", "message": "Device cannot publish for another store."}}
        )
    if evt.deviceId != device.device_id:
        raise HTTPException(
            status_code=403,
            detail={"error": {"code": "DEVICE_MISMATCH", "message": "Device identity token mismatch."}}
        )
```
This guarantees physical hardware isolation across multi-tenant retail locations.
