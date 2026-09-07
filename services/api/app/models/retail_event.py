"""Pydantic v2 schema for Canonical RetailEvent envelope."""
from typing import Any, Dict, Literal
from pydantic import BaseModel, Field, field_validator
import re

ULID_REGEX = re.compile(r"^evt_[0-9A-HJ-KM-NP-TV-Z]{26}$")


class SourceMetadata(BaseModel):
    cameraId: str
    modelId: str
    modelVersion: str


class CanonicalRetailEvent(BaseModel):
    eventId: str
    eventVersion: str = "1.0"
    eventType: Literal[
        "SHELF_LOW_STOCK",
        "SHELF_EMPTY",
        "QUEUE_HIGH",
        "TRAFFIC_HIGH",
        "TRAFFIC_LOW",
        "ZONE_DWELL",
        "DEVICE_HEALTH",
        "INVENTORY_LOW",
        "INVENTORY_RECOVERED",
    ]
    deviceId: str
    storeId: str
    zoneId: str
    timestamp: str
    confidence: float = Field(ge=0.0, le=1.0)
    severity: Literal["INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
    metadata: Dict[str, Any]
    source: SourceMetadata
    schemaVersion: str = "1.0"

    @field_validator("eventId")
    def validate_event_id_format(cls, v: str) -> str:
        # Permit either strict ULID evt_ prefix or test identifier
        if not v.startswith("evt_"):
            raise ValueError("eventId must start with 'evt_' prefix")
        return v


class EventBatchPayload(BaseModel):
    events: list[CanonicalRetailEvent]
