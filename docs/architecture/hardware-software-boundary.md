# docs/architecture/hardware-software-boundary.md — Hardware / Software Boundary Specification

> **SYSTEM BOUNDARY FREEZE**
> 
> This document strictly defines the division of responsibilities between physical edge hardware, edge software daemons, backend cloud/server platforms, and dashboard presentation clients.

---

## 1. The Core Architectural Boundary

A foundational failure mode in computer vision IoT platforms is architectural leakage: pushing heavy computer vision decoding to the cloud, or conversely, forcing edge devices to execute complex database workflows and user session management.

Retail Intelligencia freezes the hardware/software boundary according to the following strict allocation:

```mermaid
flowchart LR
    subgraph EdgeBoundary["EDGE APPLIANCE BOUNDARY (Hardware & Local SW)"]
        direction TB
        E1["Camera Acquisition (RTSP/USB)"]
        E2["Hardware Video Decoding"]
        E3["Deep Learning Inference (YOLO)"]
        E4["Object Tracking (ByteTrack)"]
        E5["Spatial Zone Projection"]
        E6["Deterministic Rule Evaluation"]
        E7["Local SQLite Buffer"]
        E8["Device Health & Thermals"]
        E9["MQTT Client Engine"]
    end

    subgraph NetworkBoundary["NETWORK BOUNDARY"]
        N1["TLS 1.3 MQTT / HTTPS"]
        N2["Canonical RetailEvent JSON"]
        N3["Health & Heartbeat Telemetry"]
        N4["Configuration Sync Payloads"]
    end

    subgraph CloudBoundary["BACKEND / DATA BOUNDARY (Cloud / Server)"]
        direction TB
        B1["Device Provisioning & Auth"]
        B2["MQTT Broker Ingestion"]
        B3["Event Validation & Deduplication"]
        B4["Data Persistence (PostgreSQL)"]
        B5["Business Rules & Escalations"]
        B6["Task Generation & Workflow Engine"]
        B7["Realtime Fan-Out (WebSocket/SSE)"]
        B8["Historical Analytics Aggregation"]
    end

    subgraph UserBoundary["USER / DASHBOARD BOUNDARY (Web Application)"]
        direction TB
        U1["Digital Twin Zone Map"]
        U2["Live Alert Triage"]
        U3["Staff Task Assignment"]
        U4["Fleet Health Monitoring"]
        U5["Store Configuration UI"]
    end

    EdgeBoundary --> NetworkBoundary
    NetworkBoundary --> CloudBoundary
    CloudBoundary --> UserBoundary
```

---

## 2. Responsibility Allocation Matrix

| System Responsibility | Edge Hardware / Software | Backend Platform (Cloud/Server) | Client Dashboard (Next.js) |
| :--- | :---: | :---: | :---: |
| **Camera RTSP/USB Connection** | **PRIMARY OWNER** | ❌ Never | ❌ Never |
| **Video Decoding & Frame Extraction**| **PRIMARY OWNER** | ❌ Never | ❌ Never |
| **Object Detection (People & Shelves)**| **PRIMARY OWNER** | ❌ Never | ❌ Never |
| **Multi-Object Tracking (ByteTrack)** | **PRIMARY OWNER** | ❌ Never | ❌ Never |
| **Polygon Zone Intersection** | **PRIMARY OWNER** | Secondary (Validation only) | Visualization only |
| **Event Debouncing & Hysteresis** | **PRIMARY OWNER** | Secondary (Cooldowns) | ❌ Never |
| **`RetailEvent` Envelope Synthesis** | **PRIMARY OWNER** | Ingestion & Schema Check | Consumer only |
| **Local Offline Storage (SQLite)** | **PRIMARY OWNER** | ❌ Never | ❌ Never |
| **Hardware Health Monitoring** | **PRIMARY OWNER** (Generates) | Consumes & Evaluates | Displays to Admin |
| **Device Provisioning & Authentication**| Requests with certs | **PRIMARY OWNER** (Issues keys) | Triggered via UI |
| **Event Persistence (PostgreSQL)** | ❌ Never | **PRIMARY OWNER** | Read-only queries |
| **Task Creation & Assignment** | ❌ Never | **PRIMARY OWNER** | Interactive execution |
| **Alert De-duplication** | Emits unique `eventId` | **PRIMARY OWNER** | Renders unique alerts |
| **Realtime Push (WebSocket/SSE)** | ❌ Never | **PRIMARY OWNER** | Subscribes & updates |
| **Store Layout & Zone Setup** | Receives via MQTT config | Persists & distributes | **PRIMARY OWNER** (Editor) |
| **Staff Task Acknowledgement** | ❌ Never | Validates & logs audit | **PRIMARY OWNER** (Staff UX) |

---

## 3. Detailed Ownership Definitions

### 3.1 Edge Node Responsibilities
The edge device is an autonomous, self-contained appliance. It is responsible for:
1. **Camera Discovery and Streaming**: Connecting to local store IP cameras via RTSP/ONVIF or local USB devices via Video4Linux (V4L2).
2. **Stream Ingestion & Decoding**: Utilizing onboard hardware video decoders (e.g. NVIDIA NVDEC or Intel VA-API) to unpack H.264/H.265 streams into raw BGR frames.
3. **Inference Execution**: Running optimized deep learning models (YOLO TensorRT/ONNX engines) for person and shelf bounding box detection.
4. **Episodic Tracking**: Running ByteTrack or SORT algorithms to correlate detections across frames, generating short-lived `track_id` values.
5. **Spatial Zone Mapping**: Projecting bottom-center foot coordinates of detected persons onto 2D polygonal floor zones.
6. **Retail Event Synthesis**: Applying deterministic thresholds (e.g., queue count > 6 for 60 seconds) to emit canonical `RetailEvent` envelopes.
7. **Resilient Buffering**: Writing events to an embedded SQLite database using Write-Ahead Logging (WAL) if upstream communication is unavailable.
8. **Hardware Telemetry**: Sampling CPU/GPU utilization, RAM, internal board temperatures, and camera frame drop rates.
9. **Outbound Communication**: Transmitting events and telemetry over TLS 1.3 MQTT to the central broker.

### 3.2 Backend Platform Responsibilities
The backend platform is the central orchestrator and system of record. It is responsible for:
1. **Device Identity & Provisioning**: Generating device credentials, validating mTLS certificates or API tokens, and maintaining device status records.
2. **Event Ingestion & Schema Enforcement**: Receiving MQTT/HTTPS payloads at the FastAPI Device Gateway and validating them against strict Pydantic schemas.
3. **Idempotency & Deduplication**: Ensuring that re-transmitted events sharing an identical `eventId` do not trigger duplicate database rows, alerts, or staff tasks.
4. **Domain Persistence**: Storing relational entities in PostgreSQL via the Node.js/TypeScript Data Service and Prisma ORM.
5. **Operational Business Rules**: Evaluating store-wide alert cooldowns, assigning priority levels, and generating actionable staff tasks.
6. **Realtime Broadcast**: Fanning out operational state changes to authenticated web clients using WebSockets and Server-Sent Events (SSE).
7. **Audit & Compliance**: Maintaining an immutable audit log of all system events, staff assignments, and task completions.

### 3.3 Dashboard Responsibilities
The Next.js web application is the human-computer interface for store managers and floor personnel. It is responsible for:
1. **Realtime Store Visualization**: Presenting a 2D floor-plan digital twin displaying live zone traffic, queue depths, and shelf stock states.
2. **Alert Management UI**: Showing prioritized operational alerts with clear contextual information (what, where, when, confidence, and recommended action).
3. **Staff Task Workflow**: Allowing floor staff to claim tasks, view instructions (e.g., "Restock Aisle 4 Cereal Shelf"), mark tasks in-progress, and complete them with resolution notes.
4. **Hardware Fleet Health View**: Allowing platform admins and store managers to monitor edge appliance thermals, CPU load, and camera feed operational status.
5. **Zone Calibration**: Providing an interactive canvas tool for store managers to draw polygon zones over reference camera stills and define operational thresholds.

---

## 4. Boundary Violation Rules

The following actions represent **critical architectural boundary violations**:
1. **DO NOT stream raw video to the backend**: Under no circumstances should continuous raw RTSP, H.264, or full-frame images be streamed to the cloud platform during normal operation.
2. **DO NOT perform cloud-based person detection**: Vision models must remain on the edge node. The backend must never be required to run object detection or tracking.
3. **DO NOT run database ORMs on the edge**: The edge node must not connect directly to the central PostgreSQL database or execute Prisma. It communicates exclusively via MQTT / HTTP APIs.
4. **DO NOT store customer PII on the edge**: The edge node must never persist customer faces, names, or persistent biometric signatures.
