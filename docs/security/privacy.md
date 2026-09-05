# docs/security/privacy.md — Privacy Architecture Specification

> **PRIVACY BY DESIGN & BIOMETRIC EXCLUSION CONSTITUTION**
> 
> Retail Intelligencia is engineered from first principles as a privacy-preserving operational platform. This document defines the privacy boundaries, biometric prohibitions, and regulatory compliance standards embedded into the architecture.

---

## 1. Privacy by Design: Core Prohibitions

To respect customer rights, prevent surveillance overreach, and comply with global privacy regulations (GDPR, CCPA/CPRA, Illinois BIPA):

```text
               ┌───────────────────────────────────────────────────────────┐
               │              THE ZERO-PII PERIMETER BOUNDARY              │
               │                                                           │
               │   ❌ NO Facial Recognition                                │
               │   ❌ NO Facial Landmark / Feature Embeddings              │
               │   ❌ NO Demographic Profiling (Age / Gender / Race)       │
               │   ❌ NO Cross-Camera Re-Identification                    │
               │   ❌ NO Customer Name or Payment Linking                  │
               │   ❌ NO Continuous Cloud Video Streaming                  │
               │                                                           │
               │   ✅ ONLY Ephemeral Bounding Boxes                        │
               │   ✅ ONLY Non-Biometric Integer Track IDs                 │
               │   ✅ ONLY Spatial Zone Aggregations (Headcounts)          │
               │   ✅ ONLY Shelf Fill Percentages                          │
               └───────────────────────────────────────────────────────────┘
```

---

## 2. Ephemeral Tracking ID Lifecycle

A frequent concern in computer vision tracking is whether a tracking ID constitutes personal data:

1. **Intra-Camera Isolation**: An `ephemeralTrackId` (e.g. `104`) is allocated by ByteTrack inside a single camera worker. It is completely isolated from other cameras in the store.
2. **In-Memory Lifespan**: The track exists solely in edge volatile RAM while the physical subject is within the optical cone of that camera.
3. **No Biometric Association**: The track stores only ground plane coordinates $(x, y)$ and bounding box dimensions. It does not store face crops, clothing embeddings, or gait signatures.
4. **Immediate Deletion**: The moment the subject walks outside the camera frame, the track is marked `LOST` and purged from memory within 3 seconds.
5. **Egress Sanitization**: The integer `track_id` is used locally to compute dwell time and queue count. Only in isolated assistance events (`ZONE_DWELL`) is the anonymous integer passed in metadata, where it has zero meaning outside that specific 2-minute window.

---

## 3. Video Containment Standard

* **Local In-Memory Processing**: Video feeds captured from store cameras are decoded into RAM surfaces, processed by TensorRT, and immediately overwritten by subsequent frames.
* **No Video Disk Caching**: The edge appliance does not maintain a continuous video DVR or rolling NVR footage buffer.
* **No Cloud Video Transmission**: Raw H.264/H.265 streams never leave the physical retail store network. The only data exiting the store are lightweight JSON event payloads.

---

## 4. Regulatory Compliance Alignment

* **GDPR (General Data Protection Regulation — EU)**:
  * By processing video locally and discarding frames without biometric extraction, Retail Intelligencia operates under the principle of **Data Minimization (Article 5(1)(c))** and **Privacy by Default (Article 25)**.
* **Illinois BIPA (Biometric Information Privacy Act — US)**:
  * The system collects **zero biometric identifiers** (no retina or iris scan, fingerprint, voiceprint, or scan of hand or face geometry).
* **CCPA / CPRA (California Consumer Privacy Act — US)**:
  * The system does not "sell" or "share" personal information, as no personal information is collected, stored, or transferred.
