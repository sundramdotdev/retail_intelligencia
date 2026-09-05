# docs/PHASE-0-CHECKLIST.md — Phase 0 Review & Approval Checklist

> This checklist serves as the formal gate review for Phase 0 (System Definition). All items must be verified and checked off prior to unlocking Phase 1.

---

## Architectural & System Governance Checklist

- [x] **System Architecture Approved**: End-to-end architecture from optical sensors to edge nodes, gateway, data service, database, realtime hub, and dashboard defined and documented in [`docs/architecture/system-architecture.md`](file:///c:/hackathon/retail_intelligencia/docs/architecture/system-architecture.md).
- [x] **Hardware/Software Boundary Approved**: Clear separation of responsibilities between edge compute appliance, cloud backend, and client dashboard defined in [`docs/architecture/hardware-software-boundary.md`](file:///c:/hackathon/retail_intelligencia/docs/architecture/hardware-software-boundary.md).
- [x] **Data Flow & Sequence Approved**: End-to-end pipeline flow (`SENSE → UNDERSTAND → DECIDE → ACT`) documented with sequence diagrams in [`docs/architecture/data-flow.md`](file:///c:/hackathon/retail_intelligencia/docs/architecture/data-flow.md).
- [x] **Service Boundaries & Stack Approved**: Strict separation of FastAPI (Device Gateway) and Node.js/TypeScript Data Service (Prisma) to PostgreSQL defined in [`docs/architecture/service-boundaries.md`](file:///c:/hackathon/retail_intelligencia/docs/architecture/service-boundaries.md).
- [x] **Failure Architecture Approved**: Handling of camera disconnects, model faults, network partitions, local SQLite buffering, and backend replay documented in [`docs/architecture/failure-architecture.md`](file:///c:/hackathon/retail_intelligencia/docs/architecture/failure-architecture.md).

---

## Contract & Protocol Checklist

- [x] **RetailEvent Contract Approved**: Canonical JSON schema, required envelope fields, types, and constraints defined in [`docs/contracts/retail-event-contract.md`](file:///c:/hackathon/retail_intelligencia/docs/contracts/retail-event-contract.md).
- [x] **Event Types Approved**: All 7 MVP event types (`SHELF_LOW_STOCK`, `SHELF_EMPTY`, `QUEUE_HIGH`, `TRAFFIC_HIGH`, `TRAFFIC_LOW`, `ZONE_DWELL`, `DEVICE_HEALTH`) documented with trigger conditions and schemas in [`docs/contracts/event-types.md`](file:///c:/hackathon/retail_intelligencia/docs/contracts/event-types.md).
- [x] **MQTT Namespace & Topics Approved**: Topic taxonomy `retail/{environment}/{storeId}/{deviceId}/...`, QoS, retention, and payload specifications documented in [`docs/contracts/mqtt-topics.md`](file:///c:/hackathon/retail_intelligencia/docs/contracts/mqtt-topics.md).
- [x] **Device Communication Protocol Approved**: Provisioning flow, heartbeat cadence, hardware health telemetry, and offline sync documented in [`docs/contracts/device-protocol.md`](file:///c:/hackathon/retail_intelligencia/docs/contracts/device-protocol.md).
- [x] **API Contracts Approved**: Complete OpenAPI/REST specification for `/api/v1` covering devices, events, stores, alerts, and tasks documented in [`docs/contracts/api-contracts.md`](file:///c:/hackathon/retail_intelligencia/docs/contracts/api-contracts.md).

---

## Hardware & Edge Computing Checklist

- [x] **Edge Device Architecture Approved**: Edge compute platform specifications, GPU/NPU acceleration, thermal limits, and storage outlined in [`docs/hardware/edge-device.md`](file:///c:/hackathon/retail_intelligencia/docs/hardware/edge-device.md).
- [x] **Camera Input Specification Approved**: RTSP, ONVIF, V4L2 USB camera stream handling, frame rates, and decoding specs documented in [`docs/hardware/camera-input.md`](file:///c:/hackathon/retail_intelligencia/docs/hardware/camera-input.md).
- [x] **Edge Input / Output Contract Approved**: Explicit definition that only raw video and config enter, and only standardized JSON leaves in [`docs/hardware/edge-input-output.md`](file:///c:/hackathon/retail_intelligencia/docs/hardware/edge-input-output.md).
- [x] **Hardware Requirements Approved**: Minimum and recommended edge hardware specifications documented in [`docs/hardware/hardware-requirements.md`](file:///c:/hackathon/retail_intelligencia/docs/hardware/hardware-requirements.md).

---

## Artificial Intelligence & Vision Checklist

- [x] **AI Architecture Approved**: Decoupled, modular multi-stage vision pipeline documented in [`docs/ai/ai-architecture.md`](file:///c:/hackathon/retail_intelligencia/docs/ai/ai-architecture.md).
- [x] **Model Responsibilities Approved**: Boundaries between person detector, shelf occupancy model, ByteTrack tracker, and deterministic rule engine defined in [`docs/ai/model-responsibilities.md`](file:///c:/hackathon/retail_intelligencia/docs/ai/model-responsibilities.md).
- [x] **Computer Vision Pipeline Approved**: Detailed frame processing, hardware decoding, inference batching, and spatial projection defined in [`docs/ai/computer-vision-pipeline.md`](file:///c:/hackathon/retail_intelligencia/docs/ai/computer-vision-pipeline.md).
- [x] **AI Safety & False Positive Suppression Approved**: Temporal debouncing, confidence thresholding, and prevention of hallucinated events documented in [`docs/ai/ai-safety.md`](file:///c:/hackathon/retail_intelligencia/docs/ai/ai-safety.md).

---

## Database, Security & Dashboard Checklist

- [x] **Database Entities Approved**: Data dictionary for Store, Device, Camera, Zone, Event, Alert, Task, and User documented in [`docs/database/entities.md`](file:///c:/hackathon/retail_intelligencia/docs/database/entities.md).
- [x] **Entity Relationships Approved**: ERD diagram and foreign key cascades defined in [`docs/database/relationships.md`](file:///c:/hackathon/retail_intelligencia/docs/database/relationships.md).
- [x] **Data Lifecycle & Retention Approved**: Retention periods, hot/cold tiers, and purge routines defined in [`docs/database/data-lifecycle.md`](file:///c:/hackathon/retail_intelligencia/docs/database/data-lifecycle.md).
- [x] **Indexing Strategy Approved**: B-tree and BRIN composite indexing for time-series queries defined in [`docs/database/indexing-strategy.md`](file:///c:/hackathon/retail_intelligencia/docs/database/indexing-strategy.md).
- [x] **Authentication Architecture Approved**: Strict separation of device mTLS / credentials from human user JWTs defined in [`docs/security/authentication-architecture.md`](file:///c:/hackathon/retail_intelligencia/docs/security/authentication-architecture.md).
- [x] **Authorization Model Approved**: Store-scoped RBAC permissions matrix documented in [`docs/security/authorization-model.md`](file:///c:/hackathon/retail_intelligencia/docs/security/authorization-model.md).
- [x] **Privacy Architecture Approved**: Zero facial recognition, zero facial embeddings, zero customer PII, and non-persistent tracking IDs documented in [`docs/security/privacy.md`](file:///c:/hackathon/retail_intelligencia/docs/security/privacy.md).
- [x] **Threat Model Approved**: STRIDE threat assessment covering physical edge, transport, API gateway, and store isolation documented in [`docs/security/threat-model.md`](file:///c:/hackathon/retail_intelligencia/docs/security/threat-model.md).
- [x] **Dashboard Information Architecture Approved**: Screen hierarchy, navigation, and visual widgets defined in [`docs/dashboard/information-architecture.md`](file:///c:/hackathon/retail_intelligencia/docs/dashboard/information-architecture.md).
- [x] **Realtime Data Architecture Approved**: WebSocket / SSE subscription channels and connection lifecycles defined in [`docs/dashboard/realtime-data.md`](file:///c:/hackathon/retail_intelligencia/docs/dashboard/realtime-data.md).
- [x] **User Role Experiences Approved**: Tailored operational views for Store Manager, Staff, and Platform Admin defined in [`docs/dashboard/user-roles.md`](file:///c:/hackathon/retail_intelligencia/docs/dashboard/user-roles.md).

---

## Repository Governance & Verification Checklist

- [x] **`memory.md` Created**: Comprehensive persistent memory file created in repository root.
- [x] **`AGENTS.md` Created**: Strict agent behavioral constitution created in repository root.
- [x] **`README.md` Created**: Project overview and roadmap created without pretending code is implemented.
- [x] **`.gitignore` Created**: Clean exclusions for node_modules, python caches, video assets, model weights, and secrets.
- [x] **No Application Feature Code Added**: Confirmed zero implementation of frontend, FastAPI routers, Prisma migrations, or model training scripts during Phase 0.
- [x] **Hardware/Software Data Boundary Unambiguous**: Validated by Hardware, Software, and Product review criteria.
