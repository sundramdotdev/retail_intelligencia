# docs/ai/computer-vision-pipeline.md — Computer Vision Pipeline Specification

> **HIGH-THROUGHPUT REAL-TIME VISION EXECUTION PIPELINE**
> 
> This document details the algorithmic and data execution pipeline of the edge vision engine, tracing frame acquisition, hardware decoding, TensorRT execution, tracking association, and spatial coordinate projection.

---

## 1. Pipeline Execution Flow

```text
[1. RTSP Stream Ingestion] ──► TCP Socket Buffer
         │
[2. Hardware Decoding]     ──► NVDEC / VA-API Hardware Decoder ──► GPU Memory Surface
         │
[3. Frame Decimation]      ──► Skip-frame worker (downsample 15fps ──► 5-10fps)
         │
[4. Preprocessing]         ──► GPU Letterbox Resize (640x640) + FP16 Normalization (0.0 - 1.0)
         │
[5. TensorRT Inference]    ──► Execution of optimized YOLO engine in FP16 / INT8
         │
[6. Postprocessing]        ──► Non-Maximum Suppression (NMS, IoU = 0.45, Conf = 0.50)
         │
[7. MOT Association]       ──► ByteTrack Kalman Filter + Hungarian matching
         │
[8. Spatial Projection]    ──► Foot Ground-Plane Coordinate Calculation (x_center, y_bottom)
         │
[9. Point-in-Polygon]      ──► Ray-Casting Algorithm across configured store zone vertices
         │
[10. State Aggregation]    ──► Temporal window counters & debounce timers
```

---

## 2. Pipeline Step Specifications

### Step 1 & 2: Ingestion & Zero-Copy Hardware Decoding
* Inbound H.264 NAL units are demuxed via FFmpeg / GStreamer pipelines.
* The compressed bitstream is fed directly into the onboard hardware decoder (e.g. NVIDIA NVDEC ASIC).
* Decoded video remains resident in unified GPU memory as an NV12 or BGR surface. **Zero CPU-to-GPU memory copy occurs.**

### Step 3 & 4: Frame Decimation & Preprocessing
* Retail store foot traffic moves at approximately 1.0 to 1.4 meters per second. Running full AI inference at 30 or 60 FPS wastes compute.
* The pipeline decimates frames to an optimal **7.5 to 10 FPS** inference rate.
* Preprocessing kernels on the GPU:
  1. Letterbox resizing to model dimensions (`640 × 640`).
  2. Color conversion from BGR to RGB.
  3. Normalization: dividing uint8 pixel values `[0..255]` by `255.0` to yield `float16` tensors in `[0.0..1.0]`.

### Step 5 & 6: TensorRT Execution & Non-Maximum Suppression (NMS)
* Inference executes using a pre-compiled TensorRT execution engine (`.engine`).
* Model runs in **FP16 precision** on Tensor Cores, achieving an average latency of **15–20 ms** per batch of 4 camera frames on Jetson Orin.
* Post-processing applies GPU-accelerated Batched NMS:
  * Confidence Threshold ($T_{conf}$): `0.50` (detections below 0.50 are discarded).
  * Intersection-over-Union Threshold ($T_{IoU}$): `0.45` (overlapping duplicate boxes collapsed).

### Step 7: ByteTrack Multi-Object Tracking
* Detections are correlated with existing tracks using a two-stage association strategy:
  1. High-confidence detections are matched against predicted Kalman filter positions.
  2. Unmatched tracks are compared against low-confidence detections (`0.10 < conf < 0.50`) to maintain track continuity through temporary occlusions (e.g., someone walking behind a pillar or another shopper).
* Unmatched tracks exceeding 30 frames (~3 seconds) of occlusion are deleted.

### Step 8 & 9: Spatial Zone Projection (Point-in-Polygon)
* To determine whether a person is standing inside an aisle or checkout queue, the system extracts the **ground-contact foot point**:
  $$x_{foot} = \frac{x_1 + x_2}{2}, \quad y_{foot} = y_2$$
* Using the foot coordinate, the spatial engine runs an optimized **Ray-Casting algorithm** against the store's configured 2D polygonal zones:
  * Returns `true` if $P(x_{foot}, y_{foot})$ lies within polygon $Z_{zoneId}$.

### Step 10: Temporal Smoothing & Hysteresis
* To prevent rapid "flickering" of events when a customer steps momentarily on a zone boundary line:
  * An entity must remain inside the polygon for at least 3 consecutive frames to be counted as `ENTERED`.
  * An entity must remain outside the polygon for at least 3 consecutive frames to be counted as `EXITED`.
