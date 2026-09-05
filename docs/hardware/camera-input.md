# docs/hardware/camera-input.md — Camera Input Specification

> **OPTICAL SENSOR INGESTION & PROTOCOL SPECIFICATION**
> 
> This document defines the technical requirements, streaming protocols, codecs, frame rates, and optical mounting standards for cameras connected to the Retail Intelligencia edge appliance.

---

## 1. Supported Camera Interfaces

The edge appliance ingests optical video feeds through two primary physical interfaces:

```text
[IP CAMERAS]  ──► RTSP / ONVIF (H.264 / H.265) ──► Gigabit Ethernet Switch ──► eth0
[USB CAMERAS] ──► V4L2 (MJPEG / YUYV)          ──► USB 3.2 Host Controller  ──► /dev/video*
```

### 1.1 IP Cameras (Network Connected)
* **Primary Protocol**: RTSP (Real-Time Streaming Protocol, RFC 2326) encapsulated over **TCP** (interleaved RTP/RTSP).
  * *Note*: UDP streaming is explicitly prohibited to prevent macroblocking and lost keyframe artifacts caused by dropped network packets.
* **Discovery & Management**: ONVIF Profile S (Open Network Video Interface Forum) for automatic camera discovery, capability interrogation, and time synchronization.
* **Authentication**: Digest Authentication over RTSP (`rtsp://user:pass@camera_ip:554/stream`).

### 1.2 USB Overhead Cameras (Direct Attached)
* **Primary Interface**: Linux Video4Linux2 (`V4L2`) driver framework.
* **Device Nodes**: Discovered and mapped via persistent udev rules (`/dev/v4l/by-id/*`).
* **Use Cases**: Overhead checkouts, self-checkout kiosks, specialized shelf endcap fixtures.

---

## 2. Video Stream Parameters & Codecs

| Parameter | Recommended Specification | Acceptable Range | Notes |
| :--- | :--- | :--- | :--- |
| **Compression Codec** | **H.264 (AVC Baseline/Main)** | H.264, H.265 (HEVC), MJPEG | H.264 offers optimal hardware decoding efficiency. |
| **Resolution** | **1920 × 1080 (1080p FHD)** | 1280 × 720 to 2560 × 1440 | 1080p provides sufficient pixel density for shelf facing analysis. |
| **Stream Frame Rate**| **15 FPS** | 10 FPS to 25 FPS | Retail human walking speed (1.2 m/s) does not require 30/60 FPS. |
| **Inference Sample Rate**| **5 to 10 FPS** (Downsampled) | 2 to 15 FPS | Skip-frame decimation conserves edge GPU compute budget. |
| **Bitrate Mode** | **CBR (Constant Bitrate)** | CBR or VBR | CBR prevents network bandwidth spikes across the camera VLAN. |
| **Bitrate Allocation**| **2.5 Mbps to 4.0 Mbps** | 1.5 Mbps to 6.0 Mbps | Balance between compression artifacts and network switch throughput. |
| **GOP / Keyframe Rate**| **1 × FPS (GOP = 15 or 30)** | 1s to 2s keyframe interval | Fast recovery from stream stalls or re-synchronization. |

---

## 3. Camera Metadata Schema

When a camera feed is registered and ingested by the edge runtime, the stream worker binds it to the following metadata structure:

```json
{
  "cameraId": "cam_aisle_04",
  "storeId": "store_001",
  "deviceId": "edge_001",
  "streamType": "RTSP",
  "streamUrl": "rtsp://192.168.100.14:554/live/stream0",
  "codec": "H264",
  "resolution": {
    "width": 1920,
    "height": 1080
  },
  "configuredFps": 15,
  "transportProtocol": "TCP",
  "mountType": "CEILING_DOWNWARD",
  "lensFocalLengthMm": 2.8,
  "lastKeyframeTimestamp": "2026-09-05T10:30:00.120Z",
  "status": "STREAMING"
}
```

---

## 4. Optical Mounting & Placement Standards

To ensure high model accuracy (>90% confidence), physical camera placement must adhere to these optical guidelines:

### 4.1 Overhead Pedestrian & Queue Cameras
* **Mounting Angle**: Steep overhead oblique (between 60° and 85° relative to the floor).
* **Mounting Height**: 3.5 meters to 5.0 meters above finished floor.
* **Benefits**: Minimizes shopper-on-shopper occlusion in crowded queue lines and yields clean foot-ground contact points for polygon zone mapping.

### 4.2 Shelf Inventory & Endcap Cameras
* **Mounting Position**: Directly opposite the target shelf bay (distance: 1.8m to 2.5m) or angled downward from ceiling above the aisle center line.
* **Field of View (FOV)**: Wide angle (85° to 110° horizontal FOV) covering 2 to 3 standard shelf bays.
* **Illumination**: Minimum 400 lux ambient retail lighting; avoiding direct glare from fluorescent ceiling fixtures into the camera lens.
