# docs/security/authorization-model.md — Authorization Model Specification

> **ROLE-BASED ACCESS CONTROL (RBAC) & STORE ISOLATION SCOPES**
> 
> This document specifies the authorization matrices, role capabilities, and tenant boundary enforcement across Retail Intelligencia.

---

## 1. Role-Based Access Control (RBAC) Roles

The platform defines three human user roles and one machine identity tier:

1. **`PLATFORM_ADMIN`**: Global infrastructure and fleet engineer. Holds system-wide administrative privileges across all retail stores and hardware appliances.
2. **`STORE_MANAGER`**: Operational commander of a specific physical store. Controls alerts, task dispatching, zone adjustments, and analytical reporting for their assigned store.
3. **`STORE_STAFF`**: In-store floor associate. Claims tasks, acknowledges operational alerts, and marks remediation actions completed.
4. **`EDGE_DEVICE`** (Machine): Automated physical appliance authorized strictly to ingest its own store configuration and emit its own sensor events.

---

## 2. Permissions Matrix

| Resource & Action | `PLATFORM_ADMIN` | `STORE_MANAGER` | `STORE_STAFF` | `EDGE_DEVICE` |
| :--- | :---: | :---: | :---: | :---: |
| **Create / Delete Stores** | ✅ ALLOWED | ❌ DENIED | ❌ DENIED | ❌ DENIED |
| **Provision / Decommission Devices**| ✅ ALLOWED | ❌ DENIED | ❌ DENIED | ❌ DENIED |
| **Inspect Device Fleet Telemetry** | ✅ Global | ✅ Own Store Only | ❌ DENIED | ❌ DENIED |
| **Calibrate Store Zones & Polygons**| ✅ ALLOWED | ✅ Own Store Only | ❌ DENIED | ❌ DENIED |
| **Read Operational Alerts** | ✅ Global | ✅ Own Store Only | ✅ Own Store Only | ❌ DENIED |
| **Acknowledge Operational Alerts** | ✅ ALLOWED | ✅ Own Store Only | ✅ Own Store Only | ❌ DENIED |
| **Create & Assign Staff Tasks** | ✅ ALLOWED | ✅ Own Store Only | ❌ DENIED | ❌ DENIED |
| **Claim / In-Progress Staff Tasks** | ✅ ALLOWED | ✅ Own Store Only | ✅ Assigned Only | ❌ DENIED |
| **Complete Staff Tasks** | ✅ ALLOWED | ✅ Own Store Only | ✅ Assigned Only | ❌ DENIED |
| **Publish `RetailEvent` Envelopes** | ❌ DENIED | ❌ DENIED | ❌ DENIED | ✅ Own Store Only |
| **Publish Device Health Telemetry**| ❌ DENIED | ❌ DENIED | ❌ DENIED | ✅ Own Store Only |
| **Consume Device Config** | ❌ DENIED | ❌ DENIED | ❌ DENIED | ✅ Own Store Only |

---

## 3. Strict Store Boundary Enforcement

### 3.1 Horizontal Tenant Boundary
* In multi-store retail enterprises, managers and staff must never view competitors' or sibling branches' data:
* In the Node.js Data Service and FastAPI Gateway, every incoming request checks the token claim:
  ```typescript
  if (user.role !== 'PLATFORM_ADMIN' && user.storeId !== request.params.storeId) {
    throw new ForbiddenException("Cross-store access is strictly prohibited.");
  }
  ```
* All database queries automatically append `AND store_id = :authenticatedStoreId`.

### 3.2 Machine Topic Guardrails
* The MQTT Broker enforces topic-level Access Control Lists (ACLs):
  ```text
  user device_edge_001
  topic read retail/prod/store_001/edge_001/config
  topic read retail/prod/store_001/edge_001/control
  topic write retail/prod/store_001/edge_001/events
  topic write retail/prod/store_001/edge_001/health
  topic write retail/prod/store_001/edge_001/heartbeat
  ```
* If `edge_001` attempts to publish to `retail/prod/store_002/...`, the MQTT broker immediately severs the TCP connection and logs a security violation.
