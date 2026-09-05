# docs/contracts/api-contracts.md — REST API Contracts Specification

> **DEVICE GATEWAY & DATA SERVICE API CONTRACTS (`/api/v1`)**
> 
> This document specifies the complete REST API interface for Retail Intelligencia, defining endpoint schemas, request/response formats, authentication policies, authorization scopes, and error behaviors.

---

## 1. Global API Conventions

* **Base Path**: `/api/v1`
* **Transport**: HTTPS (TLS 1.3 required in production)
* **Standard Headers**:
  * `Content-Type: application/json`
  * `Accept: application/json`
  * `Authorization: Bearer <token>`
  * `X-Request-ID: <uuid>` (for distributed request tracing)
* **Standard Error Envelope**:
  ```json
  {
    "error": {
      "code": "RESOURCE_NOT_FOUND",
      "message": "The requested entity does not exist.",
      "details": {},
      "timestamp": "2026-09-05T10:30:00Z",
      "requestId": "req_01J98X..."
    }
  }
  ```

---

## 2. Device Fleet Management Endpoints

### 2.1 `POST /api/v1/devices/register`
* **Purpose**: Enrolls a physical edge appliance into the store fleet.
* **Authentication**: Provisioning Token or Platform Admin JWT.
* **Authorization**: `PLATFORM_ADMIN` role or valid factory bootstrap secret.
* **Request Body**:
  ```json
  {
    "deviceId": "edge_001",
    "storeId": "store_001",
    "hardwareModel": "Jetson-Orin-NX-16GB",
    "macAddress": "00:04:4B:EA:91:22",
    "firmwareVersion": "1.0.4",
    "csr": "-----BEGIN CERTIFICATE REQUEST-----\n..."
  }
  ```
* **Response (201 Created)**:
  ```json
  {
    "deviceId": "edge_001",
    "storeId": "store_001",
    "status": "PROVISIONED",
    "certificate": "-----BEGIN CERTIFICATE-----\n...",
    "caBundle": "-----BEGIN CERTIFICATE-----\n...",
    "mqttBrokerUrl": "tls://mqtt.retail-intelligencia.io:8883"
  }
  ```
* **Error Responses**: `400 Bad Request` (invalid CSR), `409 Conflict` (deviceId already registered).

---

### 2.2 `GET /api/v1/devices/{deviceId}`
* **Purpose**: Retrieves configuration and operational state for a specific edge appliance.
* **Authentication**: Human User JWT or Authenticated Device Token.
* **Authorization**: `STORE_MANAGER`, `STORE_STAFF` (scoped to matching store), or `PLATFORM_ADMIN`.
* **Response (200 OK)**:
  ```json
  {
    "deviceId": "edge_001",
    "storeId": "store_001",
    "hardwareModel": "Jetson-Orin-NX-16GB",
    "status": "ONLINE",
    "lastHeartbeat": "2026-09-05T10:29:45Z",
    "connectedCamerasCount": 4,
    "activeZonesCount": 8
  }
  ```

---

### 2.3 `GET /api/v1/devices/{deviceId}/health`
* **Purpose**: Returns latest real-time diagnostic telemetry for the edge hardware.
* **Authentication**: Human User JWT.
* **Authorization**: `STORE_MANAGER` or `PLATFORM_ADMIN`.
* **Response (200 OK)**:
  ```json
  {
    "deviceId": "edge_001",
    "timestamp": "2026-09-05T10:30:00Z",
    "cpuUtilizationPercent": 54.2,
    "gpuUtilizationPercent": 82.0,
    "gpuTemperatureCelsius": 71.4,
    "memoryUsedMb": 5120,
    "memoryTotalMb": 8192,
    "cameras": [
      { "cameraId": "cam_01", "status": "ONLINE", "fps": 15.0, "dropRate": 0.0 }
    ]
  }
  ```

---

### 2.4 `POST /api/v1/devices/{deviceId}/heartbeat`
* **Purpose**: HTTP fallback endpoint for edge heartbeat when MQTT is blocked.
* **Authentication**: Device Bearer Token.
* **Authorization**: Bound to specific `deviceId`.
* **Request Body**:
  ```json
  {
    "timestamp": "2026-09-05T10:30:00Z",
    "uptimeSeconds": 864200,
    "status": "HEALTHY"
  }
  ```
* **Response (200 OK)**:
  ```json
  { "acknowledged": true, "timestamp": "2026-09-05T10:30:01Z" }
  ```

---

## 3. Retail Event Ingestion & Query Endpoints

### 3.1 `POST /api/v1/events`
* **Purpose**: Ingests one or more canonical `RetailEvent` envelopes over HTTPS (fallback when MQTT is disconnected).
* **Authentication**: Device Bearer Token.
* **Authorization**: Device must match `storeId` and `deviceId` in event payload.
* **Idempotency**: Strict deduplication on `eventId`. Submitting the same `eventId` repeatedly yields `200 OK` but creates zero duplicate database rows.
* **Request Body**:
  ```json
  {
    "events": [
      {
        "eventId": "evt_01J98X7Z8K3M0W4V8R9N1P2Q3R",
        "eventVersion": "1.0",
        "eventType": "QUEUE_HIGH",
        "deviceId": "edge_001",
        "storeId": "store_001",
        "zoneId": "zone_checkout_02",
        "timestamp": "2026-09-05T10:30:00Z",
        "confidence": 0.94,
        "severity": "HIGH",
        "metadata": {
          "checkoutId": "checkout_02",
          "queueCount": 8,
          "threshold": 6,
          "estimatedWaitSeconds": 240
        },
        "source": {
          "cameraId": "cam_02",
          "modelId": "person-detector-yolov8",
          "modelVersion": "1.2.0"
        },
        "schemaVersion": "1.0"
      }
    ]
  }
  ```
* **Response (200 OK)**:
  ```json
  {
    "acceptedCount": 1,
    "duplicateCount": 0,
    "rejectedCount": 0
  }
  ```

---

### 3.2 `GET /api/v1/events`
* **Purpose**: Queries historical event records with filtering and pagination.
* **Authentication**: Human User JWT.
* **Authorization**: `STORE_MANAGER`, `STORE_STAFF` (store-scoped), or `PLATFORM_ADMIN`.
* **Query Parameters**:
  * `storeId` (string, required for admin)
  * `zoneId` (string, optional)
  * `eventType` (string, optional)
  * `severity` (string, optional)
  * `startTime` (ISO-8601 UTC)
  * `endTime` (ISO-8601 UTC)
  * `limit` (int, default 50, max 200)
  * `cursor` (string, pagination cursor)
* **Response (200 OK)**:
  ```json
  {
    "items": [
      {
        "eventId": "evt_01J98X7Z8K3M0W4V8R9N1P2Q3R",
        "eventType": "QUEUE_HIGH",
        "zoneId": "zone_checkout_02",
        "timestamp": "2026-09-05T10:30:00Z",
        "severity": "HIGH",
        "confidence": 0.94
      }
    ],
    "nextCursor": "cur_01J98..."
  }
  ```

---

### 3.3 `GET /api/v1/events/{eventId}`
* **Purpose**: Retrieves complete, raw canonical payload for an individual event.
* **Authentication**: Human User JWT.
* **Response (200 OK)**: Complete canonical `RetailEvent` JSON.
* **Error Response**: `404 Not Found`.

---

## 4. Store & Zone Layout Endpoints

### 4.1 `GET /api/v1/stores`
* **Purpose**: Lists stores authorized for the authenticated user.
* **Response (200 OK)**:
  ```json
  {
    "stores": [
      {
        "storeId": "store_001",
        "name": "Market Street Superstore",
        "city": "San Francisco",
        "timezone": "America/Los_Angeles",
        "devicesCount": 3,
        "camerasCount": 12
      }
    ]
  }
  ```

---

### 4.2 `GET /api/v1/stores/{storeId}`
* **Purpose**: Retrieves store details, operating hours, and floorplan metadata.
* **Response (200 OK)**: Detailed Store JSON.

---

### 4.3 `GET /api/v1/stores/{storeId}/zones`
* **Purpose**: Returns all configured spatial polygons, detection types, and operational thresholds for a store.
* **Response (200 OK)**:
  ```json
  {
    "zones": [
      {
        "zoneId": "zone_checkout_02",
        "name": "Register 2 Queue Area",
        "type": "QUEUE",
        "cameraId": "cam_02",
        "polygon": [[120, 450], [380, 450], [400, 850], [100, 850]],
        "thresholds": {
          "queueLimit": 6,
          "durationSeconds": 60
        }
      }
    ]
  }
  ```

---

## 5. Alerts & Operational Remediation Endpoints

### 5.1 `GET /api/v1/alerts`
* **Purpose**: Lists active, unacknowledged operational alerts for the store.
* **Authentication**: Human User JWT.
* **Query Parameters**: `status` (`ACTIVE`, `ACKNOWLEDGED`, `RESOLVED`), `severity`.
* **Response (200 OK)**:
  ```json
  {
    "alerts": [
      {
        "alertId": "alt_01J98...",
        "eventId": "evt_01J98X7Z8K3M0W4V8R9N1P2Q3R",
        "storeId": "store_001",
        "zoneId": "zone_checkout_02",
        "alertType": "QUEUE_HIGH",
        "severity": "HIGH",
        "status": "ACTIVE",
        "message": "Checkout 02 Queue exceeds 6 patrons (estimated wait 240s)",
        "createdAt": "2026-09-05T10:30:00Z"
      }
    ]
  }
  ```

---

### 5.2 `POST /api/v1/alerts/{alertId}/acknowledge`
* **Purpose**: Marks an alert as acknowledged by a staff member.
* **Request Body**:
  ```json
  {
    "notes": "Opened Register 3 to absorb surge."
  }
  ```
* **Response (200 OK)**:
  ```json
  {
    "alertId": "alt_01J98...",
    "status": "ACKNOWLEDGED",
    "acknowledgedBy": "usr_staff_102",
    "acknowledgedAt": "2026-09-05T10:31:15Z"
  }
  ```

---

## 6. Staff Task Management Endpoints

### 6.1 `GET /api/v1/tasks`
* **Purpose**: Returns operational tasks for floor staff (e.g., restock, queue assistance).
* **Query Parameters**: `status` (`DETECTED`, `ASSIGNED`, `IN_PROGRESS`, `COMPLETED`), `assignedToUserId`.
* **Response (200 OK)**:
  ```json
  {
    "tasks": [
      {
        "taskId": "tsk_01J98...",
        "storeId": "store_001",
        "zoneId": "zone_aisle_04",
        "title": "Restock Beverage Shelf 04-B",
        "priority": "HIGH",
        "status": "ASSIGNED",
        "assignedTo": {
          "userId": "usr_staff_102",
          "name": "Maria Garcia"
        },
        "createdAt": "2026-09-05T10:30:00Z"
      }
    ]
  }
  ```

---

### 6.2 `POST /api/v1/tasks/{taskId}/assign`
* **Purpose**: Assigns a task to a specific staff member.
* **Request Body**:
  ```json
  {
    "assignedUserId": "usr_staff_102"
  }
  ```
* **Response (200 OK)**: Updated Task object with `status: "ASSIGNED"`.

---

### 6.3 `POST /api/v1/tasks/{taskId}/complete`
* **Purpose**: Marks a task as resolved by store personnel.
* **Request Body**:
  ```json
  {
    "resolutionNotes": "Restocked 24 units of beverage bottles from backroom inventory.",
    "unitsRestocked": 24
  }
  ```
* **Response (200 OK)**:
  ```json
  {
    "taskId": "tsk_01J98...",
    "status": "COMPLETED",
    "completedAt": "2026-09-05T10:37:20Z",
    "resolutionDurationSeconds": 440
  }
  ```
