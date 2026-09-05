# docs/PHASE-0.md — Phase 0: System Definition Charter

> **STATUS: ACTIVE / SYSTEM DEFINITION FROZEN**
> 
> Phase 0 establishes the engineering constitution and contractual boundaries for Retail Intelligencia.

---

## 1. Phase Charter & Objective

The objective of **Phase 0 — System Definition** is to eliminate all architectural, contractual, and boundary ambiguities before a single line of application software or model training code is written.

Retail Intelligencia is an edge-first, hardware-centric platform. In complex IoT and Edge AI systems, failure to freeze boundaries early leads to:
* Uncontrolled data bandwidth consumption (e.g., trying to stream raw video feeds to the cloud).
* Vendor and protocol fragmentation (e.g., ad-hoc JSON payloads created by independent teams).
* Security and privacy violations (e.g., accidental capture or leakage of customer PII).
* Fragile cloud-dependent operation (e.g., in-store systems collapsing when internet connection degrades).

Phase 0 ensures that every boundary between the physical store, camera sensors, edge hardware, edge software, device communications, backend services, databases, realtime distribution, and human staff action is explicitly defined and locked.

---

## 2. Mandatory Core Questions Answered in Phase 0

Phase 0 is considered complete only when the Hardware, Software, and Product teams have unanimous, unambiguous answers to the following operational questions:

### 2.1 Hardware Engineering Team
1. **What data enters the edge device?**
   * H.264/H.265 video streams over RTSP (IP cameras) or YUYV/MJPEG frames over V4L2 (USB cameras), alongside device-scoped configuration JSON payloads.
2. **What format does it enter in?**
   * Standardized raw video streams decoded into hardware frame buffers, and TLS-encrypted JSON configuration packets over MQTT.
3. **What processing occurs locally?**
   * Hardware decoding, frame downsampling, object detection (person & shelf), ephemeral multi-object tracking (ByteTrack), spatial zone mapping (point-in-polygon), and deterministic rule evaluation.
4. **What does the AI produce?**
   * Frame-by-frame 2D bounding boxes, confidence scores, ephemeral `track_id` coordinates, and shelf compartment occupancy percentage estimations.
5. **What does the event engine produce?**
   * Synthesized, debounced, and threshold-validated `RetailEvent` envelopes formatted strictly according to the common contract.
6. **What data leaves the edge device?**
   * Canonical `RetailEvent` JSON packets, heartbeat signals, and hardware health telemetry (CPU, GPU, RAM, thermals, stream health). **Raw video never leaves the store network.**

### 2.2 Software Engineering Team
1. **What event does the backend receive?**
   * The canonical `RetailEvent` JSON envelope.
2. **What protocol carries it?**
   * MQTT over TLS (port 8883) with QoS 1, or HTTPS POST fallback when MQTT is unavailable.
3. **What MQTT topic is used?**
   * `retail/{environment}/{storeId}/{deviceId}/events`.
4. **What schema does it follow?**
   * The common RetailEvent contract v1.0 defined in [docs/contracts/retail-event-contract.md](file:///c:/hackathon/retail_intelligencia/docs/contracts/retail-event-contract.md).
5. **How is the event validated?**
   * Validated against JSON schema and Pydantic models at the FastAPI Device Gateway.
6. **Where is it stored?**
   * Persisted to PostgreSQL by the Node.js/TypeScript Data Service using Prisma ORM.
7. **How is it deduplicated?**
   * De-duplicated using the unique `eventId` index in PostgreSQL; repeated event IDs are acknowledged and discarded without creating duplicate business entities.
8. **How is it converted into an alert/task?**
   * Backend business logic applies store-level cooldowns, severity mapping, and task assignment policies.
9. **How does the dashboard receive it?**
   * Realtime WebSockets / Server-Sent Events (SSE) push validated events and alerts to authenticated Next.js client sessions.

### 2.3 Product & Operations Team
1. **What retail problem does each event represent?**
   * `SHELF_LOW_STOCK`: Imminent product stockout risking lost revenue.
   * `SHELF_EMPTY`: Immediate shelf void causing customer disappointment and lost sales.
   * `QUEUE_HIGH`: Excessive checkout wait times causing cart abandonment.
   * `TRAFFIC_HIGH`: Surge in aisle density requiring crowd management or staff presence.
   * `TRAFFIC_LOW`: Under-utilized department or staffing misalignment.
   * `ZONE_DWELL`: Customer confusion, product indecision, or checkout bottleneck.
   * `DEVICE_HEALTH`: Hardware or camera failure degrading operational visibility.
2. **What action does the retailer take?**
   * Floor staff are dispatched to restock shelves, open additional checkout lanes, or assist browsing customers.
3. **What KPI measures the outcome?**
   * Shelf availability rate, stockout frequency, queue wait times, queue abandonment rate, staff response latency, and task resolution time.

---

## 3. Strict Non-Implementation Rule

During Phase 0, developers and autonomous AI agents are **strictly prohibited** from implementing:
* Frontend user interface or Next.js components
* FastAPI endpoint implementations or routes
* Node.js Data Service code or Prisma migrations
* Database schema execution or live PostgreSQL tables
* AI model training or inference pipelines
* MQTT broker deployment scripts
* Production Docker containers or Kubernetes manifests

Only contracts, schemas, markdown documentation, Mermaid diagrams, and configuration samples are permitted during Phase 0.
