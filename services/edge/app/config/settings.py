import os
import yaml
from pydantic_settings import BaseSettings
from pydantic import BaseModel, Field
from typing import Optional

class DeviceConfig(BaseModel):
    id: str
    name: str

class StoreConfig(BaseModel):
    id: str = "store_001"
    name: str = "Demo Store"

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

class EvaluationConfig(BaseModel):
    interval_seconds: float
    max_data_age_seconds: float

class ShelfZoneConfig(BaseModel):
    id: str
    name: str
    low_stock_threshold: float
    empty_threshold: float
    min_persistence_seconds: float
    cooldown_seconds: float

class ShelfConfig(BaseModel):
    enabled: bool
    zones: list[ShelfZoneConfig]

class QueueZoneConfig(BaseModel):
    id: str
    high_threshold: int
    recovery_threshold: int
    min_persistence_seconds: float
    cooldown_seconds: float

class QueueConfig(BaseModel):
    enabled: bool
    zones: list[QueueZoneConfig]

class TrafficZoneConfig(BaseModel):
    id: str
    window_seconds: float
    high_threshold: int
    low_threshold: int
    recovery_high_threshold: int
    recovery_low_threshold: int
    min_persistence_seconds: float
    cooldown_seconds: float

class TrafficConfig(BaseModel):
    enabled: bool
    zones: list[TrafficZoneConfig]

class DwellZoneConfig(BaseModel):
    id: str
    min_duration_seconds: float
    cooldown_seconds: float

class DwellConfig(BaseModel):
    enabled: bool
    zones: list[DwellZoneConfig]

class IntelligenceConfig(BaseModel):
    enabled: bool
    evaluation: EvaluationConfig
    shelf: ShelfConfig
    queue: QueueConfig
    traffic: TrafficConfig
    dwell: DwellConfig

class MQTTReconnectConfig(BaseModel):
    initial_delay_seconds: float = 1.0
    max_delay_seconds: float = 60.0

class MQTTConfig(BaseModel):
    enabled: bool = True
    host: str = "localhost"
    port: int = 1883
    username: Optional[str] = None
    password: Optional[str] = None
    tls: bool = False
    ca_certs: Optional[str] = None
    client_id: Optional[str] = None
    environment: str = "dev"
    keepalive_seconds: int = 30
    reconnect: MQTTReconnectConfig = Field(default_factory=MQTTReconnectConfig)

class BackendConfig(BaseModel):
    enabled: bool = True
    base_url: str = "http://localhost:8000"
    api_version: str = "v1"
    device_token: Optional[str] = None
    timeout_seconds: float = 5.0
    heartbeat_interval_seconds: int = 15

class OfflineQueueConfig(BaseModel):
    db_path: str = "data/event_queue.db"
    max_events: int = 10000
    max_storage_mb: float = 100.0
    batch_size: int = 50
    drain_rate_limit: int = 50

class Settings(BaseSettings):
    device: DeviceConfig
    store: StoreConfig = Field(default_factory=StoreConfig)
    camera: CameraConfig
    processing: ProcessingConfig
    monitoring: MonitoringConfig
    logging: LoggingConfig
    vision: VisionConfig = Field(
        default_factory=lambda: VisionConfig(
            enabled=False,
            detector=DetectorConfig(type="yolo", model="models/yolo11n.pt", confidence_threshold=0.4, iou_threshold=0.5, device="auto"),
            classes=ClassesConfig(enabled=["person"]),
            tracking=TrackingConfig(enabled=True, max_lost_frames=30)
        )
    )
    zones: list[ZoneConfig] = Field(default_factory=list)
    intelligence: IntelligenceConfig = Field(
        default_factory=lambda: IntelligenceConfig(
            enabled=False,
            evaluation=EvaluationConfig(interval_seconds=1.0, max_data_age_seconds=2.0),
            shelf=ShelfConfig(enabled=False, zones=[]),
            queue=QueueConfig(enabled=False, zones=[]),
            traffic=TrafficConfig(enabled=False, zones=[]),
            dwell=DwellConfig(enabled=False, zones=[]),
        )
    )
    mqtt: MQTTConfig = Field(default_factory=MQTTConfig)
    backend: BackendConfig = Field(default_factory=BackendConfig)
    offline_queue: OfflineQueueConfig = Field(default_factory=OfflineQueueConfig)

    class Config:
        env_nested_delimiter = '__'

def load_settings(config_path: str = "config/edge.yaml") -> Settings:
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r") as f:
        config_data = yaml.safe_load(f)

    # Ensure store exists
    if "store" not in config_data:
        config_data["store"] = {"id": "store_001", "name": "Demo Store"}

    # Override with env vars
    if os.getenv("EDGE_DEVICE_ID"):
        config_data["device"]["id"] = os.getenv("EDGE_DEVICE_ID")
    if os.getenv("STORE_ID"):
        config_data["store"]["id"] = os.getenv("STORE_ID")
    if os.getenv("CAMERA_STREAM_URL"):
        config_data["camera"]["url"] = os.getenv("CAMERA_STREAM_URL")
    if os.getenv("LOG_LEVEL"):
        config_data["logging"]["level"] = os.getenv("LOG_LEVEL")
    if os.getenv("MQTT_HOST"):
        config_data.setdefault("mqtt", {})["host"] = os.getenv("MQTT_HOST")
    if os.getenv("MQTT_PORT"):
        config_data.setdefault("mqtt", {})["port"] = int(os.getenv("MQTT_PORT"))
    if os.getenv("BACKEND_URL"):
        config_data.setdefault("backend", {})["base_url"] = os.getenv("BACKEND_URL")
    if os.getenv("DEVICE_TOKEN"):
        config_data.setdefault("backend", {})["device_token"] = os.getenv("DEVICE_TOKEN")

    return Settings(**config_data)
