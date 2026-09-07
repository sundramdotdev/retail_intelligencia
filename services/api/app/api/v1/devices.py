"""Device registration, management, and health routes."""
from typing import Any, Dict, Optional
import httpx
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.auth.device import AuthenticatedDevice, get_authenticated_device
from app.auth.human import AuthenticatedUser, get_current_user
from app.clients.data_service import data_client
from app.realtime.metrics_store import live_metrics_store

router = APIRouter(prefix="/devices", tags=["Devices"])


class DeviceRegistrationRequest(BaseModel):
    deviceId: str = Field(..., json_schema_extra={"example": "edge-dev-001"})
    storeId: str = Field(..., json_schema_extra={"example": "store_001"})
    hardwareModel: str = Field(default="Retail-Edge-AI-Node")
    macAddress: Optional[str] = Field(None, json_schema_extra={"example": "AA:BB:CC:DD:EE:FF"})
    ipAddress: Optional[str] = Field(None, json_schema_extra={"example": "192.168.1.105"})
    capabilities: Optional[Dict[str, Any]] = Field(default_factory=dict)
    provisioningKey: str = Field(...)


class HeartbeatPayload(BaseModel):
    timestamp: str
    status: Optional[str] = "ONLINE"


@router.post("/register", status_code=status.HTTP_200_OK)
async def register_device(payload: DeviceRegistrationRequest) -> Dict[str, Any]:
    """Enroll an edge device and obtain credentials & MQTT configuration."""
    if not payload.provisioningKey.startswith("prov_") and payload.provisioningKey != "demo_provisioning_key_2026":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "INVALID_PROVISIONING_KEY", "message": "Provisioning key is rejected."}},
        )

    result = await data_client.register_device(payload.model_dump())
    return {
        "deviceId": result.get("deviceId", payload.deviceId),
        "storeId": result.get("storeId", payload.storeId),
        "status": result.get("status", "PROVISIONED"),
        "mqttBrokerUrl": result.get("mqttBrokerUrl", "tls://localhost:8883"),
        "deviceToken": f"devkey_{payload.deviceId}_secret",
    }


@router.get("/{device_id}", status_code=status.HTTP_200_OK)
async def get_device(
    device_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get device configuration and current status."""
    device = await data_client.get_device(device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "DEVICE_NOT_FOUND", "message": f"Device '{device_id}' not found."}},
        )
    return device


@router.get("/{device_id}/health", status_code=status.HTTP_200_OK)
async def get_device_health(
    device_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """Check edge device connectivity and operational health."""
    device = await data_client.get_device(device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "DEVICE_NOT_FOUND", "message": f"Device '{device_id}' not found."}},
        )
    live_data = live_metrics_store.get_for_device(device_id) or {}
    
    return {
        "deviceId": device_id,
        "status": "ONLINE" if live_data and not live_data.get("isStale") else device.get("status", "OFFLINE"),
        "lastHeartbeatAt": device.get("lastHeartbeatAt"),
        "connectedCamerasCount": device.get("connectedCamerasCount", 1),
        "activeZonesCount": device.get("activeZonesCount", 3),
        "cpuUtilizationPercent": live_data.get("hardware", {}).get("cpuPercent"),
        "gpuUtilizationPercent": live_data.get("hardware", {}).get("gpuPercent"),
        "memoryUsedMb": live_data.get("hardware", {}).get("ramUsedMb"),
        "memoryTotalMb": live_data.get("hardware", {}).get("ramTotalMb"),
        "vision": live_data.get("vision"),
        "analytics": {
            "peopleNow": live_data.get("peopleNow"),
            "footfallToday": live_data.get("footfallToday"),
            "activeObjects": live_data.get("activeObjects"),
        } if live_data else None
    }


@router.post("/{device_id}/heartbeat", status_code=status.HTTP_200_OK)
async def device_heartbeat(
    device_id: str,
    payload: HeartbeatPayload,
    device: AuthenticatedDevice = Depends(get_authenticated_device),
) -> Dict[str, Any]:
    """Direct HTTP fallback endpoint for device heartbeat."""
    if device.device_id != device_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"code": "DEVICE_MISMATCH", "message": "Device cannot post heartbeat for another ID."}},
        )

    ok = await data_client.update_device_heartbeat(device_id, payload.timestamp)
    return {"status": "SUCCESS" if ok else "UNKNOWN_DEVICE", "deviceId": device_id}


@router.get("/{device_id}/stream")
async def stream_device_camera(device_id: str):
    """Proxy the live annotated MJPEG camera stream from the edge device node."""
    edge_stream_url = "http://localhost:8080/stream.mjpeg"

    async def mjpeg_proxy_generator():
        async with httpx.AsyncClient(timeout=None) as client:
            try:
                async with client.stream("GET", edge_stream_url) as response:
                    if response.status_code != 200:
                        yield b""
                        return
                    async for chunk in response.aiter_bytes():
                        yield chunk
            except Exception:
                yield b""

    return StreamingResponse(
        mjpeg_proxy_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
