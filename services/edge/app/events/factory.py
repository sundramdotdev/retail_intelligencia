import datetime
import ulid
from app.events.models import RetailEvent, SourceMetadata
from app.config.settings import Settings

class RetailEventFactory:
    def __init__(self, config: Settings):
        self.device_id = str(config.device.id) if getattr(config, 'device', None) and getattr(config.device, 'id', None) else "edge-dev-001"
        self.store_id = str(config.store.id) if getattr(config, 'store', None) and getattr(config.store, 'id', None) else "store_001"
        cam_id = getattr(config.camera, 'id', None) if getattr(config, 'camera', None) else None
        self.camera_id = str(cam_id) if cam_id else "camera-01"
        det_model = getattr(config.vision.detector, 'model', None) if getattr(config, 'vision', None) and getattr(config, 'vision', None).detector else None
        self.model_id = str(det_model) if det_model else "unknown"
        self.model_version = "1.0.0"

    def create_event(self, event_type: str, zone_id: str, severity: str, metadata: dict, confidence: float = 1.0) -> RetailEvent:
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        return RetailEvent(
            eventId=f"evt_{ulid.new().str}",
            eventVersion="1.0",
            eventType=event_type,
            deviceId=self.device_id,
            storeId=self.store_id,
            zoneId=zone_id,
            timestamp=now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
            confidence=confidence,
            severity=severity,
            metadata=metadata,
            source=SourceMetadata(
                cameraId=self.camera_id,
                modelId=self.model_id,
                modelVersion=self.model_version
            )
        )
