"""Device registration, management, and health routes."""
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.device import AuthenticatedDevice, get_authenticated_device
from app.auth.human import AuthenticatedUser, get_current_user
from app.clients.data_service import data_client

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
    return {
        "deviceId": device_id,
        "status": device.get("status", "ONLINE"),
        "lastHeartbeatAt": device.get("lastHeartbeatAt"),
        "connectedCamerasCount": device.get("connectedCamerasCount", 1),
        "activeZonesCount": device.get("activeZonesCount", 3),
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
