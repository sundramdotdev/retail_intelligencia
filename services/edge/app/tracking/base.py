from abc import ABC, abstractmethod
from typing import List
from app.models.vision import Detection, TrackedObject

class Tracker(ABC):
    @abstractmethod
    def update(self, detections: List[Detection]) -> List[TrackedObject]:
        """Update tracker with new detections and return tracked objects."""
        pass

    @property
    @abstractmethod
    def active_track_count(self) -> int:
        """Return the number of currently active tracks."""
        pass
