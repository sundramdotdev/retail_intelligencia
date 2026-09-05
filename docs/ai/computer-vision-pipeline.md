# Computer Vision Pipeline

The Retail Intelligencia edge computer implements a strictly modular, decoupled visual perception layer.

## Architecture Pipeline

```text
                 PHASE 1
                    │
              Camera / OpenCV
                    │
                    ▼
                 PHASE 2
                    │
          ┌─────────┴─────────┐
          │                   │
       YOLO11n            Norfair
     (Detection)         (Tracking)
          │                   │
          └─────────┬─────────┘
                    │
               Zone Engine
             (cv2 PolygonMath)
                    │
                    ▼
           CV OBSERVATIONS
               (Emitter)
```

## 1. Frame Ingestion
Handled by Phase 1's `VideoStreamManager`. Frames are read, validated, and passed downstream strictly according to the configured `target_fps` to avoid processing staleness.

## 2. Detection (`app.detection.base.Detector`)
The abstracted detector processes the frame and outputs `Detection` objects (class_id, label, confidence, bounding_box).
- Current Implementation: `YOLODetector` (YOLO11n).

## 3. Tracking (`app.tracking.base.Tracker`)
The abstracted tracker consumes `Detection` objects across successive frames to maintain temporal consistency, outputting `TrackedObject` entities.
- Current Implementation: `NorfairTracker` (Distance-based centroid tracker).
- Tracks are given temporary, non-identifying IDs (e.g., `#12`).

## 4. Zone Assignment (`app.zones.engine.ZoneEngine`)
Uses `cv2.pointPolygonTest` to evaluate the centroid of every `TrackedObject` against configured spatial polygons (e.g., Aisle 1, Checkout). Assigns a `current_zone`.

## 5. Observations (`app.observations.emitter.ObservationEmitter`)
Monitors the state changes of tracked objects and emits runtime CV observations:
- `PERSON_DETECTED`
- `ZONE_ENTERED`
- `ZONE_CHANGED`
- `ZONE_EXITED`

These observations establish the visual primitives required for Phase 3's retail business intelligence.
