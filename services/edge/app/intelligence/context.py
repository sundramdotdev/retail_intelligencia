from typing import List, Dict
from app.models.vision import TrackedObject, Observation
from pydantic import BaseModel

class RetailContext(BaseModel):
    timestamp: float
    device_id: str
    camera_id: str
    tracks: List[TrackedObject]
    observations: List[Observation]
    fps_metrics: Dict[str, float]
