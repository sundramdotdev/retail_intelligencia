from abc import ABC, abstractmethod
from typing import List, Optional
import numpy as np
from app.models.vision import Detection

class Detector(ABC):
    @abstractmethod
    def load(self) -> bool:
        """Initialize and load the model."""
        pass

    @abstractmethod
    def detect(self, frame: np.ndarray) -> List[Detection]:
        """Perform detection on a frame."""
        pass

    @abstractmethod
    def unload(self) -> None:
        """Release resources."""
        pass

    @property
    @abstractmethod
    def status(self) -> str:
        """Return the current status of the detector."""
        pass
