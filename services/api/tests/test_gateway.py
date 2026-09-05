"""Unit and Integration Tests for Retail Intelligencia FastAPI Device Gateway."""
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def make_valid_event(event_id="evt_01JTEST000000000000000001", store_id="store_001", device_id="edge-dev-001"):
    return {
        "eventId": event_id,
        "eventVersion": "1.0",
        "eventType": "SHELF_LOW_STOCK",
        "deviceId": device_id,
        "storeId": store_id,
        "zoneId": "zone-aisle-01",
        "timestamp": "2026-09-06T10:00:00.000Z",
        "confidence": 0.92,
        "severity": "HIGH",
        "metadata": {"stockPercentage": 15, "productCategory": "Beverages"},
        "source": {
            "cameraId": "cam-01",
            "modelId": "yolov8-shelf",
            "modelVersion": "1.2.0",
        },
        "schemaVersion": "1.0",
    }


def test_health_and_readiness():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "HEALTHY"
    assert data["service"] == "fastapi-gateway"

    resp_ready = client.get("/ready")
    assert resp_ready.status_code == 200
    assert resp_ready.json()["status"] == "READY"


def test_device_registration_success():
    payload = {
        "deviceId": "edge-dev-999",
        "storeId": "store_001",
        "hardwareModel": "Jetson-Orin-Nano",
        "provisioningKey": "demo_provisioning_key_2026",
    }
    resp = client.post("/api/v1/devices/register", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["deviceId"] == "edge-dev-999"
    assert data["storeId"] == "store_001"
    assert "deviceToken" in data


def test_device_registration_unauthorized():
    payload = {
        "deviceId": "edge-dev-hack",
        "storeId": "store_001",
        "provisioningKey": "invalid_hacker_key",
    }
    resp = client.post("/api/v1/devices/register", json=payload)
    assert resp.status_code == 401


def test_event_ingestion_success_and_deduplication():
    evt = make_valid_event("evt_01JTESTINGDEDUP0000000001")
    headers = {
        "Authorization": "Bearer devkey_edge_001_secret",
        "X-Device-ID": "edge-dev-001",
        "X-Store-ID": "store_001",
    }
    # 1. First ingestion: accepted
    resp1 = client.post("/api/v1/events", json=evt, headers=headers)
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert data1["status"] == "SUCCESS"
    assert data1["accepted"] == 1
    assert data1["duplicates"] == 0

    # 2. Re-ingestion of same eventId: duplicate detected, zero duplicate records created
    resp2 = client.post("/api/v1/events", json=evt, headers=headers)
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["status"] == "SUCCESS"
    assert data2["accepted"] == 0
    assert data2["duplicates"] == 1


def test_store_boundary_enforcement():
    """Device for store_001 attempting to send event for store_002 must be rejected."""
    evt = make_valid_event("evt_01JTESTBOUNDARY000000001", store_id="store_002")
    headers = {
        "Authorization": "Bearer devkey_edge_001_secret",
        "X-Device-ID": "edge-dev-001",
        "X-Store-ID": "store_001",
    }
    resp = client.post("/api/v1/events", json=evt, headers=headers)
    assert resp.status_code == 403
    assert "STORE_MISMATCH" in resp.json()["detail"]["error"]["code"]


def test_device_mismatch_rejection():
    """Device authenticated as edge-dev-001 attempting to send event with deviceId edge-dev-002."""
    evt = make_valid_event("evt_01JTESTDEVFAIL0000000001", device_id="edge-dev-002")
    headers = {
        "Authorization": "Bearer devkey_edge_001_secret",
        "X-Device-ID": "edge-dev-001",
        "X-Store-ID": "store_001",
    }
    resp = client.post("/api/v1/events", json=evt, headers=headers)
    assert resp.status_code == 403
    assert "DEVICE_MISMATCH" in resp.json()["detail"]["error"]["code"]


def test_invalid_event_schema_rejected():
    """Invalid eventType must fail validation."""
    evt = make_valid_event("evt_01JINVALIDTYPE0000000001")
    evt["eventType"] = "UNKNOWN_NON_DETERMINISTIC_EVENT"
    headers = {
        "Authorization": "Bearer devkey_edge_001_secret",
        "X-Device-ID": "edge-dev-001",
        "X-Store-ID": "store_001",
    }
    resp = client.post("/api/v1/events", json=evt, headers=headers)
    assert resp.status_code == 422


def test_cross_store_human_access_denied():
    """Store staff from store_001 accessing store_002 data is forbidden."""
    headers = {
        "Authorization": "Bearer staff_token_for_store_001",
    }
    resp = client.get("/api/v1/stores/store_002", headers=headers)
    assert resp.status_code == 403
    assert resp.json()["detail"]["error"]["code"] == "CROSS_STORE_ACCESS_DENIED"


def test_stores_and_zones_query():
    resp = client.get("/api/v1/stores")
    assert resp.status_code == 200
    assert "stores" in resp.json()

    resp_zones = client.get("/api/v1/stores/store_001/zones")
    assert resp_zones.status_code == 200
    assert len(resp_zones.json()["zones"]) >= 1


def test_alerts_and_acknowledgement():
    # Ingest a SHELF_EMPTY event which triggers an alert
    evt = make_valid_event("evt_01JALERTTRIGGER000000001")
    evt["eventType"] = "SHELF_EMPTY"
    headers_dev = {
        "Authorization": "Bearer devkey_edge_001_secret",
        "X-Device-ID": "edge-dev-001",
        "X-Store-ID": "store_001",
    }
    client.post("/api/v1/events", json=evt, headers=headers_dev)

    # Fetch alerts for store_001
    resp = client.get("/api/v1/alerts?storeId=store_001")
    assert resp.status_code == 200
    alerts = resp.json()["alerts"]
    assert len(alerts) >= 1

    # Acknowledge the alert
    alert_id = alerts[0]["alertId"]
    resp_ack = client.post(f"/api/v1/alerts/{alert_id}/acknowledge", json={"notes": "Checked."})
    assert resp_ack.status_code == 200
    assert resp_ack.json()["status"] == "ACKNOWLEDGED"


def test_tasks_workflow():
    # 1. Create a task
    task_payload = {
        "storeId": "store_001",
        "zoneId": "zone-aisle-01",
        "type": "RESTOCK_SHELF",
        "priority": "HIGH",
        "title": "Restock Aisle 1 Beverages",
    }
    resp = client.post("/api/v1/tasks", json=task_payload)
    assert resp.status_code == 201
    task = resp.json()
    task_id = task["taskId"]

    # 2. Assign the task
    resp_assign = client.post(f"/api/v1/tasks/{task_id}/assign", json={"assignedUserId": "usr_staff_102"})
    assert resp_assign.status_code == 200
    assert resp_assign.json()["status"] == "ASSIGNED"

    # 3. Complete the task
    resp_complete = client.post(f"/api/v1/tasks/{task_id}/complete", json={"resolutionNotes": "Restocked 12 cans."})
    assert resp_complete.status_code == 200
    assert resp_complete.json()["status"] == "COMPLETED"


def test_analytics_endpoints():
    endpoints = [
        "/api/v1/analytics/overview?storeId=store_001",
        "/api/v1/analytics/traffic?storeId=store_001",
        "/api/v1/analytics/queues?storeId=store_001",
        "/api/v1/analytics/dwell?storeId=store_001",
        "/api/v1/analytics/shelves?storeId=store_001",
    ]
    for ep in endpoints:
        resp = client.get(ep)
        assert resp.status_code == 200, f"Endpoint {ep} failed: {resp.text}"
