from abc import ABC, abstractmethod
from typing import Tuple, Optional
import numpy as np
from app.models.status import CameraState

class CameraSource(ABC):
    def __init__(self, camera_id: str):
        self.camera_id = camera_id
        self._state = CameraState.DISCONNECTED

    @property
    def state(self) -> CameraState:
        return self._state

    @abstractmethod
    def connect(self) -> bool:
        """Connect to the camera source."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the camera source."""
        pass

    @abstractmethod
    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Read a frame from the camera."""
        pass

    def is_connected(self) -> bool:
        return self._state in (CameraState.CONNECTED, CameraState.STREAMING)

    @abstractmethod
    def get_metadata(self) -> dict:
        """Return metadata about the stream (e.g., fps, resolution)."""
        pass
