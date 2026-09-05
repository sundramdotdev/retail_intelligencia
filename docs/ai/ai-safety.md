# docs/ai/ai-safety.md — AI Safety & False Positive Suppression Specification

> **RELIABILITY, CALIBRATION & HALLUCINATION PREVENTION**
> 
> Operational store managers quickly lose trust in automated platforms if flooded with false alarms. This document specifies the mathematical and heuristic safeguards employed to suppress false positives, prevent data fabrication, and calibrate confidence scores.

---

## 1. Absolute Rule Against Fabrication

> **CORE SAFETY DIRECTIVE**
> 
> Under no operational circumstance may the edge appliance or backend service fabricate synthetic detections, simulate bounding boxes, or emit mock retail events to mask an offline camera, failing model, or sensor disconnection.
> 
> If a sensor is unavailable, the state must explicitly report `SENSOR_UNAVAILABLE`. Real-time operational intelligence must reflect genuine physical observations only.

---

## 2. False Positive Mitigation Strategies

Retail stores present intense visual noise: moving shopping carts, children in strollers, reflections on polished vinyl floors, shadows from changing overhead lights, and store mannequins. The following mitigations are enforced:

### 2.1 Temporal Debouncing & Hysteresis
Single-frame anomalies must never trigger an operational alert.
* **Queue Congestion Debouncing**:
  * A queue length threshold breach (e.g. `count >= 6`) must be sustained continuously for **at least 60 seconds** before a `QUEUE_HIGH` event is synthesized.
  * *Hysteresis Reset*: The alert is only cleared when the queue drops below `threshold - 2` (e.g., $\le 4$ persons) for at least 30 seconds, preventing rapid alert flapping.
* **Shelf Stockout Debouncing**:
  * A shelf empty condition must be observed continuously for **at least 15 seconds** to ensure the condition is not a customer reaching in and momentarily blocking the camera's view of the product facing.

### 2.2 Ground-Plane Foot Contact Filtering
* Measuring bounding box centers often creates false zone intersections because a tall person standing outside an aisle can cast their upper body into the camera's zone polygon.
* **Mandatory Standard**: Zone membership is evaluated strictly on the **bottom-center coordinate** ($x_{foot}, y_{foot}$), which maps directly to the store floor tile plane.

### 2.3 Aspect Ratio & Size Sanity Checks
* False positive person detections caused by shopping carts, cardboard standees, or floor reflections are filtered using anthropometric physical constraints:
  * Person bounding box aspect ratio ($Height / Width$) must fall between $1.5$ and $4.2$.
  * Bounding box area must exceed minimum pixel threshold (e.g., $> 32 \times 64$ pixels) based on calibrated ceiling camera distance.

---

## 3. Confidence Calibration & Minimum Cutoffs

| Pipeline Stage | Minimum Confidence Cutoff | Operational Action if Below Cutoff |
| :--- | :---: | :--- |
| **Person Detector (Primary)** | **0.50** | Detections below 0.50 are discarded from primary track creation. |
| **ByteTrack Occlusion Buffer**| **0.15** | Used only to retain existing tracks through occlusions; never creates new tracks. |
| **Shelf Occupancy Estimator** | **0.70** | If confidence < 0.70 (e.g. bad lighting or lens glare), state is marked `UNCERTAIN`. |
| **`RetailEvent` Emission Floor**| **0.80** | Synthesized `RetailEvent` envelopes must carry an aggregated confidence $\ge 0.80$. |

---

## 4. Visual Occlusion Handling

```mermaid
flowchart TD
    D1["Person Detected (Conf > 0.80)"] --> T1["Active Track Established"]
    T1 --> O1{"Person Walks Behind Display Pillar<br/>(Visual Detection Lost)"}
    O1 -->|Frame 1-15 (0-1.5s)| K1["Kalman Filter Projects Velocity<br/>Track Retained in Memory"]
    O1 -->|Frame 16-30 (1.5-3.0s)| K2["ByteTrack Matches Low-Conf Detection (Conf > 0.15)<br/>Track Maintained"]
    O1 -->|Frame > 30 (> 3.0s)| D2["Track Marked LOST & Terminated<br/>Zone Exit Event Processed"]
```

---

## 5. Drift and Shadow Rejection

* **Shadow Elimination**: Preprocessing color normalization (HSV/LAB space conversion) dampens dark floor shadows cast by ceiling spotlights.
* **Stationary Object Rejection**: If a detected object exhibits zero movement over 15 minutes (velocity $\approx 0$), the tracker flags the item as a static store prop (e.g., advertising cutout or mannequin) and removes it from pedestrian traffic counts.
