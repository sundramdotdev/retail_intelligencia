from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class Detection(BaseModel):
    class_id: int
    label: str
    confidence: float
    bounding_box: List[float]  # [x1, y1, x2, y2]
    timestamp: float

class TrackedObject(BaseModel):
    track_id: int
    label: str
    confidence: float
    bounding_box: List[float]  # [x1, y1, x2, y2]
    center: Dict[str, float]   # {"x": float, "y": float}
    first_seen: float
    last_seen: float
    age: int
    current_zone: Optional[str] = None

class Observation(BaseModel):
    type: str # PERSON_DETECTED, OBJECT_DETECTED, ZONE_ENTERED, ZONE_CHANGED, ZONE_EXITED
    track_id: Optional[int] = None
    zone_id: Optional[str] = None
    timestamp: float
    metadata: Dict[str, Any] = {}
