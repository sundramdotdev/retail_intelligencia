from typing import Optional, Dict
from enum import Enum
from pydantic import BaseModel, Field

class DeviceState(str, Enum):
    STARTING = "STARTING"
    READY = "READY"
    STREAMING = "STREAMING"
    DEGRADED = "DEGRADED"
    ERROR = "ERROR"
    STOPPING = "STOPPING"

class CameraState(str, Enum):
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    STREAMING = "STREAMING"
    DEGRADED = "DEGRADED"
    ERROR = "ERROR"

class CameraInfo(BaseModel):
    id: str
    status: CameraState
    url: Optional[str] = None
    type: str

class SystemHealth(BaseModel):
    cpu_usage_percent: float
    memory_usage_percent: float
    memory_available_bytes: int
    disk_usage_percent: float
    gpu_usage_percent: Optional[float] = None
    gpu_memory_usage: Optional[float] = None
    gpu_temperature: Optional[float] = None

class DeviceInfo(BaseModel):
    device_id: str
    status: DeviceState
    camera: CameraInfo
    health: Optional[SystemHealth] = None
    timestamp: str

class FrameInfo(BaseModel):
    frame_id: int
    capture_timestamp: float
    processing_timestamp: float

class DetectionResult(BaseModel):
    label: str
    confidence: float
    bounding_box: list[float]  # [x, y, w, h]
    timestamp: float

class FPSMetrics(BaseModel):
    input_fps: float
    processing_fps: float
