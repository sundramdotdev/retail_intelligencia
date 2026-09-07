import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app

client = TestClient(app)

def test_device_stream_endpoint_headers():
    response = client.get("/api/v1/devices/edge-dev-001/stream")
    assert response.status_code == 200
    assert "multipart/x-mixed-replace" in response.headers.get("content-type", "")
    assert response.headers.get("cache-control") == "no-cache, no-store, must-revalidate"
