# Retail Intelligencia

> **Hardware-First Edge AI Retail Intelligence Platform**
> 
> Real-time physical store operational intelligence powered by on-premise edge computing nodes, transforming camera streams into actionable retail tasks without compromising customer privacy.

---

## 1. Platform Overview

**Retail Intelligencia** bridges the physical reality of retail stores with modern operational execution. In a typical supermarket or grocery store, millions of dollars are lost annually due to shelf stockouts, unmanaged checkout congestion, and poor floor staff allocation. Traditional solutions either require costly manual audits or attempt to upload high-bandwidth customer video streams to cloud servers—introducing latency, extreme bandwidth costs, and severe privacy risks.

Retail Intelligencia deploys dedicated **physical Edge AI compute appliances** directly into the retail store network. Connected to existing IP cameras (via RTSP) and local USB cameras, the edge hardware decodes video feeds, executes computer vision models (person detection, multi-object tracking, shelf occupancy estimation), and evaluates deterministic retail rules locally.

When an operational condition is detected—such as an empty cereal shelf or an expanding queue at checkout 3—the edge node emits a standardized, lightweight JSON packet called a **`RetailEvent`**. This event is transmitted securely via MQTT to the cloud platform, which validates the event, updates the store's digital twin, triggers staff alerts, and assigns actionable tasks to store managers and floor personnel in real time.

```text
PHYSICAL STORE ──► CAMERAS ──► EDGE AI NODE ──► RETAIL EVENT ──► BACKEND ──► DASHBOARD ──► STAFF ACTION
```

---

## 2. Hardware-First Core Positioning

Retail Intelligencia is **NOT** a generic cloud SaaS dashboard with mock AI. 

The **physical edge appliance is the primary product**. The software backend, database, and web dashboard exist solely to:
1. Provision and configure physical edge devices.
2. Ingest, validate, and persist high-velocity edge intelligence.
3. Enforce store-level business policies and alert routing.
4. Provide store managers and floor staff with a live operational command center.

### The Sense-Understand-Decide-Act Loop
* **SENSE**: In-store optical sensors capture real-world store conditions.
* **UNDERSTAND**: Edge hardware extracts spatial bounding boxes, object tracks, and occupancy heuristics.
* **DECIDE**: Deterministic edge rule engines evaluate conditions against store thresholds.
* **ACT**: Backend distributes prioritized remediation tasks to human retail staff.

---

## 3. Architecture Blueprint

```text
                         RETAIL STORE
                              │
                ┌─────────────┴─────────────┐
                │                           │
             IP Cameras                USB Cameras
                │                           │
                └─────────────┬─────────────┘
                              │
                              ▼
                 ┌────────────────────────┐
                 │      EDGE AI NODE      │
                 │                        │
                 │ Video Ingestion        │
                 │ OpenCV / Decoder       │
                 │ AI Inference           │
                 │ Object Detection       │
                 │ Object Tracking        │
                 │ Zone Engine            │
                 │ Retail Event Engine    │
                 │ Local Event Buffer     │
                 │ Device Health          │
                 └────────────┬───────────┘
                              │
                        MQTT / HTTPS
                              │
                              ▼
                 ┌────────────────────────┐
                 │     DEVICE GATEWAY     │
                 │        FastAPI         │
                 └────────────┬───────────┘
                              │
              ┌───────────────┼────────────────┐
              │                                │
              ▼                                ▼
     ┌──────────────────┐             ┌─────────────────┐
     │   Data Service   │             │ Realtime Layer  │
     │   Node.js / TS   │             │  WebSocket/SSE  │
     │      Prisma      │             └────────┬────────┘
     └────────┬─────────┘                      │
              │                                │
              ▼                                │
     ┌──────────────────┐                      │
     │    PostgreSQL    │                      │
     └──────────────────┘                      │
                                               ▼
                                      ┌────────────────┐
                                      │ Next.js Web UI │
                                      └───────┬────────┘
                                              │
                                              ▼
                                        STORE MANAGER
                                              │
                                              ▼
                                         STORE STAFF
```

---

## 4. Current Status: Phase 0 (System Definition)

> **Notice**: The repository is currently in **Phase 0 — System Definition**. 
> 
> In accordance with project governance, **NO application feature code** (FastAPI services, Next.js frontend, Prisma migrations, model weights, or cloud deployments) is built during Phase 0. 
> 
> Phase 0 establishes the unambiguous architectural constitution, formal event contracts, hardware specifications, database schemas, security boundaries, and agent governance rules. Implementation begins only upon Phase 0 sign-off.

See the complete [Phase 0 Checklist](file:///c:/hackathon/retail_intelligencia/docs/PHASE-0-CHECKLIST.md) and [Phase 0 Specification](file:///c:/hackathon/retail_intelligencia/docs/PHASE-0.md).

---

## 5. Development Roadmap

* 🟢 **Phase 0 — System Definition**: Architecture freeze, data contracts, API specifications, and hardware-software boundaries. **(COMPLETE)**
* ⚪ **Phase 1 — Repository & Development Infrastructure**: Monorepo orchestration, toolchains, linting, CI/CD, local dev containers.
* ⚪ **Phase 2 — Edge Device Foundation**: Embedded Linux setup, hardware acceleration runtimes (TensorRT, V4L2, GStreamer), system daemons.
* ⚪ **Phase 3 — Computer Vision Runtime**: Person detector, shelf occupancy model, ByteTrack tracking pipeline, spatial calibration.
* ⚪ **Phase 4 — Retail Intelligence Engine**: Deterministic heuristic rules, queue estimator, dwell monitor, `RetailEvent` generator.
* ⚪ **Phase 5 — Device Communication**: TLS MQTT client, SQLite WAL offline buffer, auto-reconnect, heartbeat & health telemetry daemons.
* ⚪ **Phase 6 — Backend & Data Platform**: FastAPI ingestion gateway, Node.js/TypeScript Data Service, Prisma ORM, PostgreSQL.
* ⚪ **Phase 7 — Realtime Dashboard**: Next.js command center, interactive store zone map, WebSocket/SSE live feed.
* ⚪ **Phase 8 — Staff Action System**: Operational alert dispatching, mobile task triage, acknowledgement workflows.
* ⚪ **Phase 9 — Analytics, Testing, Optimization & Deployment**: End-to-end load testing, hardware thermal validation, pilot readiness.

---

## 6. Repository Documentation Map

All architectural and engineering specifications are organized under the [`docs/`](file:///c:/hackathon/retail_intelligencia/docs) directory:

```text
retail_intelligencia/
│
├── AGENTS.md                                   # Agent operational instructions
├── memory.md                                   # Persistent single source of truth
├── README.md                                   # Project introduction & roadmap
├── .gitignore                                  # Environment & binary ignore patterns
│
└── docs/
    ├── PHASE-0.md                              # Phase 0 charter & exit criteria
    ├── PHASE-0-CHECKLIST.md                    # Phase 0 review checklist
    ├── PHASE-0-COMPLETION.md                   # Phase 0 formal sign-off report
    │
    ├── architecture/                           # System architecture & boundaries
    │   ├── system-architecture.md
    │   ├── hardware-software-boundary.md
    │   ├── data-flow.md
    │   ├── service-boundaries.md
    │   └── failure-architecture.md
    │
    ├── contracts/                              # Formal data and protocol contracts
    │   ├── retail-event-contract.md
    │   ├── event-types.md
    │   ├── mqtt-topics.md
    │   ├── device-protocol.md
    │   └── api-contracts.md
    │
    ├── hardware/                               # Edge hardware and camera specs
    │   ├── edge-device.md
    │   ├── camera-input.md
    │   ├── edge-input-output.md
    │   └── hardware-requirements.md
    │
    ├── ai/                                     # Computer vision & model specs
    │   ├── ai-architecture.md
    │   ├── model-responsibilities.md
    │   ├── computer-vision-pipeline.md
    │   └── ai-safety.md
    │
    ├── database/                               # Database entities & lifecycle
    │   ├── entities.md
    │   ├── relationships.md
    │   ├── data-lifecycle.md
    │   └── indexing-strategy.md
    │
    ├── security/                               # Auth, permissions & privacy
    │   ├── authentication-architecture.md
    │   ├── authorization-model.md
    │   ├── privacy.md
    │   └── threat-model.md
    │
    └── dashboard/                              # UI/UX information architecture
        ├── information-architecture.md
        ├── realtime-data.md
        └── user-roles.md
```

---

## 7. Developer & Agent Rules

All contributors (human or AI) must strictly follow the rules in [AGENTS.md](file:///c:/hackathon/retail_intelligencia/AGENTS.md) and [memory.md](file:///c:/hackathon/retail_intelligencia/memory.md):
1. **Never build features out of phase.**
2. **Never stream raw video to the cloud.**
3. **Never implement facial recognition or persistent customer re-identification.**
4. **Never execute Prisma from Python.**
5. **Always preserve the canonical `RetailEvent` contract.**
