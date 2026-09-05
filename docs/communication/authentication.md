# Communication Security & Authentication Architecture

Retail Intelligencia implements zero-trust security between physical edge AI nodes and cloud/on-premise backend services.

---

## 1. Authentication Layers

```text
┌─────────────────────────────────┐
│       PHYSICAL EDGE NODE        │
└────────────────┬────────────────┘
                 │
                 │ 1. Mutual TLS (mTLS) / X.509 Device Certificate
                 │    or Bearer Hardware Token (devkey_*)
                 ▼
┌─────────────────────────────────┐
│     ECLIPSE MOSQUITTO BROKER    │
│  & FASTAPI INGESTION GATEWAY    │
└────────────────┬────────────────┘
                 │
                 │ 2. Internal Service Secret (X-Internal-Secret)
                 ▼
┌─────────────────────────────────┐
│     TYPESCRIPT DATA SERVICE     │
└────────────────┬────────────────┘
                 │
                 │ 3. Strictly Isolated Prisma DB Connection
                 ▼
┌─────────────────────────────────┐
│       POSTGRESQL DATABASE       │
└─────────────────────────────────┘
```

---

## 2. Device Identity & Hardware Tokens

Each registered physical device has a cryptographically randomized device token:
* **Token Format**: `devkey_{deviceId}_{randomSecret}`
* **Header Transmission**:
  ```http
  Authorization: Bearer devkey_edge_001_secret
  X-Device-ID: edge-dev-001
  X-Store-ID: store_001
  ```
* **Store Boundary Verification**:
  The FastAPI Gateway validates that `X-Device-ID` and `X-Store-ID` strictly match the device record in the system. Any attempt by a compromised node to publish events on behalf of a different store or device ID is rejected with `HTTP 403 Forbidden` (`STORE_MISMATCH` or `DEVICE_MISMATCH`).

---

## 3. Mutual TLS (mTLS) for MQTT in Production

In production retail deployments:
1. Every edge appliance contains a TPM 2.0 chip or secure element storing its private key.
2. The Mosquitto broker enforces `require_certificate true`.
3. Client certificates are verified against the Enterprise Retail CA root.
4. Edge nodes connect via port `8883` over TLS v1.3.

---

## 4. Internal Service-to-Service Boundary

The FastAPI Device Gateway and TypeScript Data Service communicate via an internal network.
* All requests between the Gateway and Data Service require the `X-Internal-Secret` header.
* Direct public ingress to the TypeScript Data Service is blocked at the reverse proxy/firewall layer.
