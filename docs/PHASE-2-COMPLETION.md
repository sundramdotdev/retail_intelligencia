# Phase 2 Completion Report

## Overview
Phase 2 (Computer Vision Engine) has been fully implemented. The Edge node has been upgraded from a basic frame-capture pipeline to a robust, modular visual perception system. It performs object detection, tracks objects temporarily across frames, assigns them to configured spatial zones, and emits high-level computer vision observations.

## Architecture
The vision pipeline operates sequentially on incoming frames from Phase 1:
```text
Camera (Phase 1)
 ↓
OpenCV Frame
 ↓
YOLO11n (Detector)
 ↓
Detection Objects
 ↓
Norfair (Tracker)
 ↓
Zones (cv2 polygon math)
 ↓
Observations (Emitter)
```

## Model
- **Model**: YOLO11n (Ultralytics)
- **Version**: YOLOv11 nano
- **Provisioning Method**: Automated fallback provisioning via `ultralytics`. If `yolo11n.pt` is not found, the detector fetches it and caches it locally without redundant downloads.
- **Supported Classes**: Filtered dynamically via `edge.yaml`. Currently tracking `person`, `bottle`, `cup`, and `backpack`.
- **Limitations**: YOLO11n is a generic detector. The provided classes are standard COCO classes and **must not be interpreted as retail product intelligence**. True retail intelligence (e.g., detecting "Coke" or "Low Stock") will require a custom-trained model in future phases.

## Tracking
- **Tracker**: `norfair` (A lightweight, distance-based centroid tracker).
- **Lifecycle**: Tracks initialize after a brief delay, remain active, and are dropped after `max_lost_frames` (30 frames) of no detection.
- **Temporary ID Policy**: Track IDs (e.g., #12) are ephemeral and strictly localized to the current runtime session. No persistent facial recognition or identity mapping is performed, adhering to strict privacy requirements.

## Zones
- **Geometry Strategy**: Standard 2D cartesian coordinates (pixels) mapped via OpenCV's `cv2.pointPolygonTest` using the tracked object's centroid.
- **Configuration**: Fully configurable via `edge.yaml`.
- **Transition Behavior**: The system tracks the last known zone for each object and emits `ZONE_ENTERED`, `ZONE_CHANGED`, or `ZONE_EXITED` events upon transitions.

## Performance
*Note: True performance benchmarking requires execution on actual physical edge hardware. The below is the baseline recorded.*
- **Input FPS**: ~30 FPS
- **Processing FPS**: Capped at 10 FPS
- **Inference FPS**: ~9.9 FPS
- **Latency**: ~65ms (CPU inference fallback)

## Hardware Validation
The pipeline gracefully integrates with the Phase 1 mobile network camera stream.
When `display.enabled: true` is configured, an OpenCV visualization window overlays:
- Input/Processing/Inference FPS
- Model Inference Latency
- Polygons with corresponding Zone Names
- Bounding boxes with Temporary IDs and assigned Zones

## Object Detection Observability
A dedicated Object Detection screen has been introduced to visually debug the raw generic model output independently of zones and intelligence processing. 
- Launched via `python -m app.main --object-detection`
- Bypasses Tracking and Zones to focus entirely on YOLO bounding box confidence.
- Dynamically renders true model capabilities.

## Known Limitations
- The `pip install ultralytics` dependency can be heavy and take significant time to fetch in constrained network environments.
- YOLO11n provides generic object detection only.
- GPU acceleration requires appropriate local CUDA drivers which are abstracted here via `device: auto`.

## Not Implemented
As strictly required by the phase boundary, the following were **NOT** implemented:
- Retail event engine (e.g., Queue/Shelf intelligence)
- Traffic intelligence or analytics
- MQTT communication
- Database (PostgreSQL/Prisma)
- Backend API (FastAPI) or Dashboard (Next.js)
- Cloud AI or Facial Recognition
- LLM Integration

## Next Phase
**Phase 3 — Retail Event Engine**
