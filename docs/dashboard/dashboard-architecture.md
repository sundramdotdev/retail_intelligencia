# Phase 6 & 7: Dashboard and Staff Action System

## Overview
The Retail Intelligencia Real-Time Dashboard is a Next.js application that provides operational observability for physical retail stores. It serves as the primary interface for Store Managers and Store Staff to monitor edge AI detections and manage resulting tasks.

Phase 6 built the real-time observability layer, and Phase 7 built the staff action system. Both are integrated into the same Next.js front-end.

## Tech Stack
*   **Framework**: Next.js 14+ (App Router)
*   **Language**: TypeScript
*   **Styling**: Tailwind CSS v4 (Custom Dark Editorial Design System)
*   **Data Fetching**: TanStack Query
*   **Real-time Transport**: Server-Sent Events (SSE) via FastAPI gateway
*   **Icons**: Lucide React
*   **Charts**: Recharts

## Architectural Design

### 1. Real-time Architecture (SSE)
Unlike traditional polling dashboards, this system is entirely event-driven, reflecting the `Hardware → MQTT → Backend → UI` pipeline.
*   **Backend Broadcaster**: FastAPI maintains in-memory asynchronous queues for connected clients. When the MQTT Consumer receives an event, it injects it into the SSE Broadcaster queue.
*   **SSE Client**: The React application uses a robust `EventSource` wrapper (`src/lib/sse-client.ts`) that handles automatic exponential backoff reconnection.
*   **Cache Invalidation Hook**: The `RealtimeProvider` component listens to SSE messages. When an event arrives (e.g., `QUEUE_HIGH`), the provider automatically triggers TanStack Query to invalidate and refetch the relevant caches (e.g., `['events']`, `['alerts']`, `['tasks']`). This keeps the UI fresh without manual polling and guarantees that the UI matches the truth stored in PostgreSQL.

### 2. State Management
*   **Server State**: TanStack Query manages all API data (alerts, tasks, events, metrics).
*   **UI State**: React Local State (`useState`) for filters and UI toggles.
*   **Auth State**: A development-mode role selector (`AuthProvider` in `src/lib/auth.ts`) simulates `STORE_MANAGER`, `STORE_STAFF`, and `PLATFORM_ADMIN` roles.

### 3. Key Components

*   **Store Map (`store-map.tsx`)**: A dynamic 2D SVG representation of the store layout. It colors zones based on their type (e.g., Shelves are green/amber, Queues are blue/red) and maps real-time data to physical space.
*   **Event Feed (`event-feed.tsx`)**: A scrolling timeline of raw AI inferences (e.g., `QUEUE_HIGH`) directly from the edge devices, annotated with confidence scores and zones.
*   **Alert Card & Task Card**: UI representations of the state machines defined in Phase 5. They provide role-based action buttons (e.g., "Acknowledge Alert", "Start Task", "Complete Task").

## The Staff Action Lifecycle (Phase 7)
The system moves from passive observability to active management via the Task system:
1.  **Detection**: Edge AI fires `RetailEvent` via MQTT.
2.  **Alerting**: Backend Rules Engine escalates the event to an `ACTIVE` Alert.
3.  **Task Creation**: A Store Manager reviews the alert and creates a `Task` (e.g., "Restock Aisle 4").
4.  **Assignment**: The Task is assigned to a Staff member (`ASSIGNED`).
5.  **Execution**: The Staff member marks it `IN_PROGRESS` and eventually `COMPLETED`.

## Directory Structure
```text
src/
├── app/                  # Next.js App Router Pages
│   ├── dashboard/        # Operational Screens
│   │   ├── alerts/       
│   │   ├── analytics/    
│   │   ├── devices/      
│   │   ├── live/         
│   │   ├── tasks/        
│   │   └── zones/        
│   ├── login/            # Dev Role Selector
│   ├── globals.css       # Tailwind v4 Design System
│   └── layout.tsx        
├── components/
│   └── dashboard/        # Core UI Components
├── hooks/                # TanStack Query Wrappers
├── lib/
│   ├── api-client.ts     # Typed REST API Client
│   ├── sse-client.ts     # SSE Reconnection Logic
│   ├── auth.tsx          # Dev Auth Context
│   ├── types.ts          # Shared Interface Contracts
│   └── utils.ts          # Formatting Helpers
└── providers/            # React Context Providers
```
