import datetime
from ulid import ULID
from app.events.models import RetailEvent, SourceMetadata
from app.config.settings import Settings

class RetailEventFactory:
    def __init__(self, config: Settings):
        self.device_id = config.device.id
        self.store_id = config.store.id
        self.camera_id = config.camera.id
        self.model_id = config.vision.detector.model if config.vision.enabled else "unknown"
        self.model_version = "1.0.0"

    def create_event(self, event_type: str, zone_id: str, severity: str, metadata: dict, confidence: float = 1.0) -> RetailEvent:
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        return RetailEvent(
            eventId=f"evt_{str(ULID())}",
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
