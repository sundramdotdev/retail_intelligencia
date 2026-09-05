# Model Selection: YOLO11n

## Overview
For Phase 2 of Retail Intelligencia, we have selected **YOLO11n** (Ultralytics) as the initial development detector.

## Why YOLO11n for Phase 2?
Phase 2 aims to establish the **visual perception layer**—handling video frames, performing generic object detection, applying multi-object tracking, and mapping coordinates to configured store zones.
YOLO11n provides an excellent balance of speed and accuracy for edge hardware. Its small footprint allows it to run smoothly even on CPU constraints (such as Raspberry Pi 5 or low-power Intel nodes), while remaining fully compatible with CUDA/TensorRT acceleration.

## Model Provisioning Process
The application utilizes Ultralytics' built-in auto-download mechanism. Upon startup, the `YOLODetector` instance checks for the configured model (e.g., `models/yolo11n.pt`). If missing, it fetches the weights from the Ultralytics release repository and caches them locally. It is strictly configured not to download on every startup if the weights already exist, avoiding redundant bandwidth usage and allowing offline operation.

## Supported Classes and Configuration
YOLO11n is pretrained on the COCO dataset (80 generic classes).
In our `edge.yaml`, we use a `classes.enabled` filter to whitelist only specific classes:
- `person`
- `bottle`
- `cup`
- `backpack`

During initialization, the edge runtime validates these configured strings against the model's loaded `.names` dictionary.

## Inference Details
- **Confidence Threshold**: 0.40 (Configurable)
- **IoU Threshold**: 0.50 (Configurable)
- **Inference Device**: The `device: auto` configuration detects CUDA availability; if not present, it gracefully falls back to CPU.

## Limitations
**YOLO11n is a generic detector.** Its pretrained classes **must not be interpreted as production retail product classes.** While it can detect a generic "bottle" or "cup," it cannot differentiate between "Coke" and "Pepsi," nor can it determine if an item is a specific brand of shampoo.

## Future Custom-Model Strategy
Production shelf and product intelligence (Phase 3+) will require appropriate retail-specific training and modeling. 
The system architecture was explicitly designed to keep the detector abstracted. The `Detector` abstract base class means `yolo11n.pt` can be cleanly swapped with a custom `retail_model.pt` without modifying the downstream tracker, zone engine, or observation layers.
