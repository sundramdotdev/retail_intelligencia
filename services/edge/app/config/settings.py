import os
import yaml
from pydantic_settings import BaseSettings
from pydantic import BaseModel, Field
from typing import Optional

class DeviceConfig(BaseModel):
    id: str
    name: str

class CameraConfig(BaseModel):
    id: str
    name: str
    type: str
    url: Optional[str] = None
    device_index: Optional[int] = 0

class ProcessingConfig(BaseModel):
    target_fps: int
    resize_width: int
    resize_height: int
    display_enabled: bool = False

class HealthThresholds(BaseModel):
    cpu_warning_percent: float
    cpu_critical_percent: float
    memory_warning_percent: float
    memory_critical_percent: float
    disk_warning_percent: float
    disk_critical_percent: float

class MonitoringConfig(BaseModel):
    health_interval_seconds: int
    fps_window_seconds: int
    health: HealthThresholds

class LoggingConfig(BaseModel):
    level: str

class DetectorConfig(BaseModel):
    type: str
    model: str
    confidence_threshold: float
    iou_threshold: float
    device: str

class ClassesConfig(BaseModel):
    enabled: list[str]

class TrackingConfig(BaseModel):
    enabled: bool
    max_lost_frames: int

class VisionConfig(BaseModel):
    enabled: bool
    detector: DetectorConfig
    classes: ClassesConfig
    tracking: TrackingConfig

class ZoneConfig(BaseModel):
    id: str
    name: str
    enabled: bool
    polygon: list[list[int]]

class Settings(BaseSettings):
    device: DeviceConfig
    camera: CameraConfig
    processing: ProcessingConfig
    monitoring: MonitoringConfig
    logging: LoggingConfig
    vision: VisionConfig
    zones: list[ZoneConfig]

    class Config:
        env_nested_delimiter = '__'

def load_settings(config_path: str = "config/edge.yaml") -> Settings:
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r") as f:
        config_data = yaml.safe_load(f)

    # Override with env vars
    if os.getenv("EDGE_DEVICE_ID"):
        config_data["device"]["id"] = os.getenv("EDGE_DEVICE_ID")
    if os.getenv("CAMERA_STREAM_URL"):
        config_data["camera"]["url"] = os.getenv("CAMERA_STREAM_URL")
    if os.getenv("LOG_LEVEL"):
        config_data["logging"]["level"] = os.getenv("LOG_LEVEL")

    return Settings(**config_data)
