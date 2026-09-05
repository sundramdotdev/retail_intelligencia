# docs/security/threat-model.md — Threat Model Specification (STRIDE)

> **THREAT ASSESSMENT, ATTACK SURFACE & MITIGATION STRATEGY**
> 
> Physical edge appliances deployed in publicly accessible retail stores present unique attack surfaces. This document applies the STRIDE methodology to analyze threats and specify technical defenses.

---

## 1. Attack Surface Analysis

The Retail Intelligencia system presents four primary attack surfaces:

1. **Physical Edge Appliance**: Exposed hardware in store backrooms, ceilings, or network closets.
2. **Camera In-Store Network (VLAN)**: Optical feeds, RTSP streams, and PoE switches.
3. **Transport Layer (MQTT/HTTPS)**: Telemetry streams traveling across the public internet to cloud brokers.
4. **Backend Gateway & Presentation API**: Ingestion endpoints, REST APIs, and WebSocket hubs.

---

## 2. STRIDE Threat Assessment & Countermeasures

### 2.1 Spoofing (Identity Impersonation)
* **Threat 1**: An attacker connects an unauthorized laptop to the store network and transmits fake `RetailEvent` envelopes to trigger false alerts.
  * **Mitigation**: The MQTT broker requires mutual TLS (mTLS) with client certificates signed by the dedicated platform CA. The FastAPI fallback gateway requires a 256-bit cryptographically random device token.
* **Threat 2**: An attacker attempts to forge human user JWTs to access management dashboards.
  * **Mitigation**: JWTs are signed with asymmetric keys (RS256/EdDSA) using private keys stored in cloud KMS. Public keys are rotated periodically via JWKS endpoints.

### 2.2 Tampering (Data Alteration)
* **Threat 1**: Man-in-the-Middle (MitM) modification of `RetailEvent` payloads (e.g. altering confidence or severity).
  * **Mitigation**: All communications require mandatory TLS 1.3 with modern cipher suites (AES-GCM / ChaCha20-Poly1305). Insecure HTTP and plaintext MQTT are permanently rejected.
* **Threat 2**: Tampering with the edge appliance firmware or local storage.
  * **Mitigation**: UEFI Secure Boot, TPM 2.0 measured boot, and a cryptographically verified read-only root filesystem (dm-verity).

### 2.3 Repudiation (Denial of Actions)
* **Threat 1**: Floor staff claims they never acknowledged an alert or marked a task completed.
  * **Mitigation**: All task status transitions record an immutable audit row containing `userId`, `storeId`, exact UTC timestamp, and user IP address.
* **Threat 2**: An edge appliance denies emitting a specific event.
  * **Mitigation**: Every event carries a unique monotonic ULID `eventId` and is logged in the local WAL buffer alongside device hardware signatures.

### 2.4 Information Disclosure (Data Leakage)
* **Threat 1**: Eavesdropping on customer video feeds.
  * **Mitigation**: In-store cameras are isolated on a dedicated, non-routable private camera VLAN (VLAN 100). Cameras have zero access to WAN. Video feeds never exit the local store network.
* **Threat 2**: Exposing cross-store operational performance metrics.
  * **Mitigation**: Strict database tenant scoping where all queries enforce `storeId` constraints based on authenticated token claims.

### 2.5 Denial of Service (DoS)
* **Threat 1**: Telemetry storm caused by a malfunctioning or compromised edge appliance flooding the MQTT broker with millions of messages.
  * **Mitigation**: EMQX / Mosquitto rate-limiting and connection throttling (max 100 messages/sec per device). Payloads exceeding 64 KB are dropped immediately.
* **Threat 2**: Network partition between store and cloud.
  * **Mitigation**: Local SQLite WAL ring buffer on the edge appliance stores up to 5,000,000 events locally without data loss.

### 2.6 Elevation of Privilege
* **Threat 1**: Floor staff modifies API parameters to grant themselves `PLATFORM_ADMIN` privileges.
  * **Mitigation**: Role claims are validated server-side in the Node.js Data Service against the signed JWT. Role elevation endpoints are accessible exclusively to existing `PLATFORM_ADMIN` tokens with multi-factor authentication (MFA).
