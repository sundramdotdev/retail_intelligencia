from pydantic import BaseModel, Field
from typing import Dict, Any

class SourceMetadata(BaseModel):
    cameraId: str
    modelId: str
    modelVersion: str

class RetailEvent(BaseModel):
    eventId: str
    eventVersion: str
    eventType: str
    deviceId: str
    storeId: str
    zoneId: str
    timestamp: str
    confidence: float
    severity: str
    metadata: Dict[str, Any]
    source: SourceMetadata
    schemaVersion: str = "1.0"
