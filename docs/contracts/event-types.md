# docs/contracts/event-types.md — Approved Event Types Specification

> **MVP EVENT CATALOG & OPERATIONAL TAXONOMY**
> 
> This document details the 7 approved event types for Retail Intelligencia MVP. For every event type, this catalog establishes the business purpose, optical sources, trigger thresholds, metadata schemas, severity mappings, and downstream operational actions.

---

## 1. Summary of MVP Event Types

| Event Type | Focus Domain | Primary Trigger Metric | Default Severity | Downstream Action |
| :--- | :--- | :--- | :---: | :--- |
| **`SHELF_LOW_STOCK`** | Inventory / Merchandising | Shelf fill < threshold (e.g. 25%) | `MEDIUM` | Restock shelf compartment |
| **`SHELF_EMPTY`** | Inventory / Merchandising | Shelf fill == 0% | `HIGH` | Immediate restock / alert manager |
| **`QUEUE_HIGH`** | Checkout Operations | Headcount > limit (e.g. 6 persons) | `HIGH` | Open adjacent register |
| **`TRAFFIC_HIGH`** | Floor Safety / Traffic | Shopper density > surge threshold | `INFO` / `MEDIUM` | Allocate floor assistance |
| **`TRAFFIC_LOW`** | Floor Utilization | Shopper density < idle threshold | `INFO` | Adjust staffing schedule |
| **`ZONE_DWELL`** | Shopper Engagement | Individual dwell time > threshold | `LOW` / `MEDIUM` | Staff customer assistance |
| **`DEVICE_HEALTH`** | Hardware & Fleet Ops | Thermal / stream / resource warning| `HIGH` / `CRITICAL`| IT / hardware maintenance |

---

## 2. Event Type Specifications

### 2.1 `SHELF_LOW_STOCK`
* **Purpose**: Identifies when retail product facings on a monitored shelf have depleted below a critical threshold, enabling just-in-time replenishment before total stockout.
* **Optical Source**: Overhead or facing shelf camera; Shelf Occupancy Model (CNN segmentation/bounding surface).
* **Trigger Condition**: Measured `occupancyPercentage <= threshold` continuously for a debounce window of 15 seconds (to eliminate transient hand occlusions).
* **Confidence Meaning**: Model confidence in shelf surface segmentation and void detection (0.0 to 1.0).
* **Severity Behavior**:
  * `occupancyPercentage` between 15% and 25%: `LOW`
  * `occupancyPercentage` < 15%: `MEDIUM`
* **Metadata Schema**:
  ```json
  {
    "shelfId": "shelf_04_b",
    "productCategory": "Beverages",
    "occupancyPercentage": 18.5,
    "threshold": 25.0,
    "facingCount": 2,
    "debounceSeconds": 15
  }
  ```
* **Consumer**: Node.js Data Service (Alert/Task Engine) ──► Floor Staff Restock Queue.
* **Resulting Action**: Dispatches an aisle replenishment task to floor staff with shelf and aisle coordinates.

---

### 2.2 `SHELF_EMPTY`
* **Purpose**: Identifies a complete stockout condition where an entire shelf section or SKU facing is completely bare.
* **Optical Source**: Overhead or facing shelf camera; Shelf Occupancy Model.
* **Trigger Condition**: Measured `occupancyPercentage == 0%` continuously for a debounce window of 10 seconds.
* **Confidence Meaning**: Statistical certainty that zero product units occupy the designated shelf bounding box.
* **Severity Behavior**:
  * Default: `HIGH`. If in high-margin promotion endcap: `CRITICAL`.
* **Metadata Schema**:
  ```json
  {
    "shelfId": "shelf_02_endcap",
    "productCategory": "Dairy",
    "occupancyPercentage": 0.0,
    "threshold": 0.0,
    "emptyFacings": 4,
    "debounceSeconds": 10
  }
  ```
* **Consumer**: Data Service ──► Store Manager & Inventory Lead.
* **Resulting Action**: Urgent audio/visual notification on manager dashboard; high-priority task dispatched to stockroom runner.

---

### 2.3 `QUEUE_HIGH`
* **Purpose**: Detects checkout bottleneck conditions where the line length exceeds acceptable customer service standards.
* **Optical Source**: Overhead checkout camera; Person Detector (YOLO) + ByteTrack Multi-Object Tracker.
* **Trigger Condition**: Number of tracked persons whose ground-plane foot coordinates fall within the checkout queue polygon exceeds `threshold` (default: 6 persons) for greater than `durationSeconds` (default: 60 seconds).
* **Confidence Meaning**: Mean detection confidence of the persons tracked within the queue boundary.
* **Severity Behavior**:
  * Queue count 6–8 persons: `HIGH`
  * Queue count > 8 persons or wait time > 300s: `CRITICAL`
* **Metadata Schema**:
  ```json
  {
    "checkoutId": "checkout_03",
    "queueCount": 8,
    "threshold": 6,
    "durationSeconds": 75,
    "estimatedWaitSeconds": 280,
    "activeRegister": true
  }
  ```
* **Consumer**: Data Service ──► Store Front-End Manager.
* **Resulting Action**: Generates immediate alert: "Queue Surge at Register 3 — Open Register 4 immediately."

---

### 2.4 `TRAFFIC_HIGH`
* **Purpose**: Identifies surges in pedestrian foot traffic inside specific store zones (e.g., entrance, promotional aisle, bakery).
* **Optical Source**: Overhead camera; Person Detector + Spatial Zone Engine.
* **Trigger Condition**: Total unique shoppers inside zone polygon exceeds `capacityThreshold` within an aggregated rolling window (e.g., 30 persons / 60 seconds).
* **Confidence Meaning**: Aggregated detection reliability of tracked pedestrian tracks.
* **Severity Behavior**:
  * Surges under 150% capacity: `INFO`
  * Surges > 150% capacity (fire/crowd concern): `MEDIUM`
* **Metadata Schema**:
  ```json
  {
    "trafficCount": 42,
    "capacityThreshold": 25,
    "windowSeconds": 60,
    "averageVelocity": 0.65
  }
  ```
* **Consumer**: Data Service ──► Analytics Pipeline & Floor Lead.
* **Resulting Action**: Alerts store security or floor marshals to assist customer flow.

---

### 2.5 `TRAFFIC_LOW`
* **Purpose**: Identifies abnormally low foot traffic in high-priority zones during standard operating hours, signaling poor merchandising or operational anomalies.
* **Optical Source**: Overhead camera; Person Detector + Spatial Zone Engine.
* **Trigger Condition**: Foot traffic falls below `minimumExpectedThreshold` for longer than 30 consecutive minutes during active store hours.
* **Confidence Meaning**: Certainty that camera stream is active and operational while observing zero or near-zero occupants.
* **Severity Behavior**: Fixed at `INFO`.
* **Metadata Schema**:
  ```json
  {
    "trafficCount": 1,
    "expectedMinimum": 10,
    "durationMinutes": 35,
    "storeOperatingHours": true
  }
  ```
* **Consumer**: Data Service ──► Analytics Engine.
* **Resulting Action**: Logged for operational review and labor optimization; no urgent staff dispatch.

---

### 2.6 `ZONE_DWELL`
* **Purpose**: Identifies shoppers experiencing extended dwell times in high-consideration zones (e.g. cosmetics, infant care, electronics) indicating potential customer confusion or intent to purchase requiring assistance.
* **Optical Source**: Overhead aisle camera; Person Detector + ByteTrack Tracker.
* **Trigger Condition**: A single tracked entity's `dwellSeconds` within a defined assistance polygon exceeds `thresholdSeconds` (e.g., > 120 seconds) without moving toward checkout.
* **Confidence Meaning**: Tracking continuity confidence (Kalman filter track stability).
* **Severity Behavior**: Fixed at `LOW` (assistance prompt) or `MEDIUM` (> 240s).
* **Metadata Schema**:
  ```json
  {
    "ephemeralTrackId": 389,
    "dwellSeconds": 145.2,
    "thresholdSeconds": 120.0,
    "department": "Baby Care"
  }
  ```
* **Consumer**: Data Service ──► Department Associate.
* **Resulting Action**: Dispatches an assistance prompt to department staff: "Customer browsing in Baby Care for > 2 minutes — check if assistance is required."

---

### 2.7 `DEVICE_HEALTH`
* **Purpose**: Edge appliance internal telemetry reporting operational status, thermals, model performance, and stream stability.
* **Optical Source**: Edge operating system, hardware sensors, RTSP watchdog daemon.
* **Trigger Condition**:
  * Routine heartbeat: Every 60 seconds (Status: OK).
  * Threshold breach: CPU > 90%, GPU Temp > 85°C, Camera dropped frames > 15%, or stream disconnect.
* **Confidence Meaning**: Fixed at 1.0 (Direct OS metric).
* **Severity Behavior**:
  * Routine heartbeat: `INFO`
  * Resource warning / single camera drop: `HIGH`
  * System overheating / storage failure: `CRITICAL`
* **Metadata Schema**:
  ```json
  {
    "status": "WARNING",
    "uptimeSeconds": 864200,
    "cpuUtilizationPercent": 74.2,
    "gpuUtilizationPercent": 88.0,
    "memoryUsedMb": 6144,
    "memoryTotalMb": 8192,
    "gpuTemperatureCelsius": 86.5,
    "storageUsedMb": 18400,
    "storageAvailableMb": 45000,
    "cameras": [
      { "cameraId": "cam_01", "status": "ONLINE", "fps": 14.9, "droppedFramesPercent": 0.2 },
      { "cameraId": "cam_02", "status": "OFFLINE", "fps": 0.0, "droppedFramesPercent": 100.0 }
    ],
    "models": [
      { "modelId": "person-detector-yolov8", "status": "RUNNING", "avgInferenceMs": 18.4 }
    ]
  }
  ```
* **Consumer**: Data Service ──► Platform Administrator & Store Manager.
* **Resulting Action**: Flags device in fleet dashboard, triggers technician alert if hardware parameters exceed safety bounds.
