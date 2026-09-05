# docs/architecture/system-architecture.md — System Architecture Specification

> **RETAIL INTELLIGENCIA ARCHITECTURAL CONSTITUTION**
> 
> This document defines the canonical end-to-end system architecture of Retail Intelligencia, establishing the structural relationships between physical hardware sensors, edge computing nodes, communication buses, backend services, persistence layers, realtime event distribution, and user action interfaces.

---

## 1. Architectural Philosophy: Hardware-First Physical AI

Retail Intelligencia is designed as a **hardware-first edge AI system**. The physical edge computing appliance deployed inside the retail store is the core operational engine. The system operates on the fundamental principle:

```text
PHYSICAL STORE ──► SENSE ──► UNDERSTAND ──► DECIDE ──► ACT
```

1. **Physical Store**: The real-world retail environment containing shoppers, aisles, shelves, checkout lanes, and inventory.
2. **Sense**: Optical sensors (IP cameras over RTSP and USB cameras over V4L2) continuously observe the physical scene.
3. **Understand**: Dedicated on-premise edge AI hardware captures, decodes, and runs deep neural network models (person detection, multi-object tracking, and shelf occupancy estimation).
4. **Decide**: The edge retail rule engine correlates detections across spatial zones and time windows, evaluating deterministic thresholds to produce canonical `RetailEvent` envelopes.
5. **Act**: The cloud/on-premise backend persists the event, evaluates business escalation policies, generates alerts, and dispatches real-time tasks to store managers and floor personnel.

---

## 2. Canonical Architecture Diagram

```mermaid
flowchart TD
    subgraph PhysicalStore["PHYSICAL STORE ENVIRONMENT"]
        subgraph OpticalSensors["Optical Sensors"]
            CamIP["IP Cameras (RTSP/ONVIF)"]
            CamUSB["USB Overhead Cameras (V4L2)"]
        end
        
        subgraph HumanActors["Store Personnel"]
            StoreMgr["Store Manager (Command Dashboard)"]
            FloorStaff["Floor Staff (Mobile/Tablet Task Triage)"]
        end
    end

    subgraph EdgeHardware["EDGE COMPUTING NODE (On-Premise Appliance)"]
        subgraph IngestionDec["Stream Ingestion & Decoding"]
            RTSPClient["RTSP/V4L2 Client"]
            HWDecoder["Hardware Video Decoder (NVDEC/VAAPI)"]
        end
        
        subgraph EdgeAI["Edge Computer Vision Engine"]
            PersonDet["Person Detector (YOLO/TensorRT)"]
            ShelfDet["Shelf Occupancy Detector"]
            MOT["Multi-Object Tracker (ByteTrack)"]
            ZoneEngine["Spatial Zone Engine (Polygon Mapping)"]
        end
        
        subgraph EdgeCore["Edge Intelligence & Reliability"]
            RuleEngine["Deterministic Retail Rule Engine"]
            LocalBuffer[("Local SQLite Event Buffer (WAL)")]
            HealthDaemon["Device Health & Telemetry Daemon"]
            MQTTClient["MQTT Client (TLS 1.3 / mTLS)"]
        end
    end

    subgraph NetworkTransport["DEVICE COMMUNICATION LAYER"]
        MQTTBroker["MQTT Message Broker (EMQX / Mosquitto)"]
        HTTPSFallback["HTTPS Fallback Gateway"]
    end

    subgraph BackendCloud["BACKEND SERVICES PLATFORM"]
        FastAPIGW["Device Gateway Service (Python / FastAPI)"]
        DataService["Data Service (Node.js / TypeScript)"]
        PrismaORM["Prisma ORM"]
        PostgresDB[("PostgreSQL Relational Database")]
        RealtimeHub["Realtime Notification Hub (WebSocket / SSE)"]
    end

    subgraph PresentationLayer["PRESENTATION & ACTION LAYER"]
        NextJSApp["Retail Intelligencia Web UI (Next.js)"]
    end

    %% Flow connections
    CamIP -->|"RTSP Stream (H.264/H.265)"| RTSPClient
    CamUSB -->|"Raw Frames (MJPEG/YUYV)"| RTSPClient
    RTSPClient --> HWDecoder
    HWDecoder -->|"Decoded BGR Frames"| PersonDet
    HWDecoder -->|"Decoded BGR Frames"| ShelfDet
    PersonDet -->|"Bounding Boxes"| MOT
    MOT -->|"Ephemeral Track IDs"| ZoneEngine
    ShelfDet -->|"Surface Fill %"| ZoneEngine
    ZoneEngine -->|"Zone Occupancy & Dwell"| RuleEngine
    RuleEngine -->|"Synthesized RetailEvent"| LocalBuffer
    HealthDaemon -->|"Heartbeat & Health Metrics"| LocalBuffer
    LocalBuffer -->|"Drained In-Order Events"| MQTTClient
    
    MQTTClient -->|"TLS MQTT (QoS 1)"| MQTTBroker
    MQTTClient -.->|"Offline HTTPS Replay"| HTTPSFallback
    
    MQTTBroker -->|"Topic Subscription"| FastAPIGW
    HTTPSFallback --> FastAPIGW
    FastAPIGW -->|"Validated Internal Events"| DataService
    DataService --> PrismaORM
    PrismaORM --> PostgresDB
    DataService -->|"Operational Triggers"| RealtimeHub
    
    RealtimeHub -->|"WebSocket / SSE Push"| NextJSApp
    NextJSApp -->|"Visual Alerts & Live Map"| StoreMgr
    NextJSApp -->|"Assigned Action Tasks"| FloorStaff
    FloorStaff -->|"Task Acknowledgement & Resolution"| NextJSApp
    NextJSApp -->|"API Mutations"| DataService
```

---

## 3. Layer-by-Layer Architectural Breakdown

### 3.1 Physical Store & Sensor Ingestion Layer
* **IP Cameras**: Standard security and surveillance cameras streaming RTSP over the local store VLAN.
* **USB Overhead Cameras**: Direct plug-and-play USB cameras covering checkout lanes or specific display endcaps.
* **Stream Decoupling**: Streams are decoded in-memory using dedicated hardware acceleration (e.g., NVDEC on NVIDIA platforms or VA-API on x86). Raw frames are never written to disk or transmitted over WAN.

### 3.2 Edge AI Hardware Node (Appliance)
* **Compute Platform**: Ruggedized on-premise industrial PC or AI compute module (e.g., NVIDIA Jetson Orin or Intel Core Ultra with discrete NPU/GPU).
* **Vision Models**:
  * *Person Detection*: Identifies shoppers, staff, and queue lines.
  * *Shelf Occupancy*: Evaluates shelf compartment fill percentages.
  * *Tracking*: Maintains temporary spatial continuity (`track_id`) solely across consecutive frames to compute dwell times and queue progressions.
* **Zone Engine**: Projects image-space coordinates into calibrated floor-plan polygonal zones (e.g., `zone_aisle_04`, `zone_checkout_02`).
* **Retail Rule Engine**: Evaluates state machines and debounced threshold logic to generate canonical `RetailEvent` envelopes.
* **Local Buffer**: Embedded SQLite database operating in Write-Ahead Logging (WAL) mode. Buffers all generated events locally so that zero data is lost during store internet disconnections.

### 3.3 Device Communication Layer
* **Primary Protocol**: MQTT 5.0 / 3.1.1 over TLS (port 8883) with mutual certificate authentication (mTLS) or per-device pre-shared cryptographic tokens.
* **Topic Structure**: Hierarchical namespace `retail/{environment}/{storeId}/{deviceId}/...` ensuring complete tenant and store isolation.
* **Quality of Service (QoS)**: QoS 1 (At least once delivery) for events and health telemetry; QoS 0 for high-frequency heartbeats; QoS 2 for remote device control commands.

### 3.4 Backend Services Platform
* **Device Gateway (FastAPI)**: Lightweight, high-throughput Python service responsible for validating inbound MQTT and HTTPS payloads against strict Pydantic schemas, managing device registration, and ingesting telemetry.
* **Data Service (Node.js / TypeScript)**: Core domain business logic, task workflow orchestration, alert escalation, and database interface via Prisma ORM.
* **Database (PostgreSQL)**: Fully normalized relational persistence storing stores, devices, zones, canonical events, alerts, tasks, and audit logs.
* **Realtime Hub**: Low-latency notification layer broadcasting live updates via WebSocket or SSE to authenticated dashboard clients.

### 3.5 Presentation & Human Action Layer
* **Next.js Web Application**: Server-rendered and client-hydrated responsive command center providing:
  * Store digital twin and zone heatmap.
  * Real-time operational alert feeds.
  * Staff task dispatch and lifecycle tracking.
  * Device fleet health and camera monitoring.

---

## 4. Fundamental Architectural Invariants

Every component and engineer on the platform must maintain the following architectural invariants:

1. **Zero Video Egress**: Raw video frames and high-rate video streams **must never exit the physical retail store network** during standard operations. Only metadata JSON packets leave the store.
2. **Edge Independence**: The edge node must be fully autonomous. If the cloud backend, internet connection, or local router fails, edge inference and event buffering continue unabated.
3. **Canonical Event Unification**: No component may create an alternative event envelope. Every edge-generated insight must match the common `RetailEvent` contract.
4. **Service Boundary Separation**: FastAPI is the device gateway; Node.js/TypeScript is the data domain service. Python services must never directly execute Prisma ORM commands.
5. **No Biometrics or Re-Identification**: Tracking IDs are ephemeral and strictly intra-camera. Facial recognition and customer profiling are permanently prohibited.
