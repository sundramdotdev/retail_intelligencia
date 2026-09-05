# docs/hardware/hardware-requirements.md — Hardware Requirements Specification

> **EDGE COMPUTE, SENSOR & NETWORK INFRASTRUCTURE STANDARDS**
> 
> This document specifies the minimum and recommended physical infrastructure required to operate Retail Intelligencia inside a commercial supermarket or retail store.

---

## 1. Edge Appliance Compute Specifications

| Component | Minimum Specification (4–8 Cameras) | Recommended Specification (12–24 Cameras) |
| :--- | :--- | :--- |
| **Architecture** | ARM64 or x86_64 | ARM64 or x86_64 |
| **Host Processor (CPU)** | 6-Core ARM Cortex-A78AE / Intel Core i5 (12th Gen+) | 12-Core ARM Cortex-A78AE / Intel Core i7 / Xeon E-2300 |
| **AI Accelerator (GPU/NPU)**| NVIDIA Orin (40 TOPS INT8) / Intel Arc A380 | NVIDIA Orin AGX (200–275 TOPS) / NVIDIA RTX A2000 12GB |
| **Hardware Video Decoder** | Dedicated 1080p60 H.264/H.265 ASIC decoder | Dual 4K60 / Multi-stream 1080p240 ASIC decoders |
| **System Memory (RAM)** | 8 GB Unified LPDDR5 / DDR4 ECC | 16 GB – 32 GB LPDDR5 / DDR5 ECC |
| **Local Storage (NVMe)** | 128 GB Industrial PCIe NVMe (300 TBW endurance) | 512 GB Industrial PCIe NVMe (1,000 TBW endurance) |
| **Network Interfaces** | Dual 1GbE Ethernet (RJ45) | Dual 2.5GbE / 10GbE SFP+ |
| **Hardware Security** | TPM 2.0 cryptoprocessor | TPM 2.0 cryptoprocessor + Secure Boot |
| **Power Consumption** | 15W – 25W (Passive Fanless) | 40W – 75W (Industrial PWM Fan) |
| **Operating Temperature** | 0°C to +50°C ambient | -10°C to +60°C ambient |

---

## 2. In-Store Network Infrastructure Requirements

To prevent camera stream latency, frame drops, and cross-talk with store Point-of-Sale (POS) systems, the physical in-store network must satisfy the following criteria:

### 2.1 Managed Network Switch
* **Switch Type**: Managed L2/L3 Gigabit Ethernet Switch with 802.3at (PoE+) support.
* **Power Budget**: Minimum 30W per camera port; total PoE budget ≥ 250W for a 16-port deployment.
* **Switching Capacity**: Non-blocking backplane with minimum 32 Gbps switching capacity to handle uncompressed intra-switch routing.

### 2.2 VLAN Segmentation
The store network must configure two physically or logically isolated Virtual LANs:
1. **Camera VLAN (VLAN 100)**:
   * Dedicated to IP cameras and `eth0` of the edge appliance.
   * DHCP server isolated to the camera subnet (`192.168.100.0/24`).
   * No gateway routing to the public internet (air-gapped from WAN).
2. **Management & Uplink VLAN (VLAN 200)**:
   * Connects `eth1` of the edge appliance to the store router.
   * Access to external internet strictly restricted to outbound TCP port 8883 (MQTT TLS) and TCP port 443 (HTTPS).

---

## 3. Physical Installation & Enclosure Guidelines

1. **Mounting Location**:
   * Preferred: Standard 19-inch equipment rack inside the store IT/telecom server room.
   * Alternative: Lockable NEMA-rated steel ceiling-mount enclosure located within 90 meters of camera PoE runs.
2. **Power Protection**:
   * The edge appliance and camera switch must be powered through an Uninterruptible Power Supply (UPS) rated for minimum 1000VA / 600W.
   * UPS must sustain at least 15 minutes of runtime during store power blinks to permit safe WAL buffer synchronization.
3. **Thermal Clearances**:
   * Minimum 50mm airflow clearance on all sides of the heat sink.
   * Enclosures deployed in non-air-conditioned backrooms must feature filtered fan ventilation.
