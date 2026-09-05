import pytest
import numpy as np
from app.camera.base import CameraSource
from app.models.status import CameraState
from typing import Tuple, Optional

class MockCamera(CameraSource):
    def __init__(self, camera_id: str, succeed_connect: bool = True, return_frame: bool = True):
        super().__init__(camera_id)
        self.succeed_connect = succeed_connect
        self.return_frame = return_frame

    def connect(self) -> bool:
        if self.succeed_connect:
            self._state = CameraState.CONNECTED
            return True
        else:
            self._state = CameraState.ERROR
            return False

    def disconnect(self) -> None:
        self._state = CameraState.DISCONNECTED

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        if not self.is_connected():
            return False, None
        
        if self.return_frame:
            self._state = CameraState.STREAMING
            # Mock a 10x10 frame
            return True, np.zeros((10, 10, 3), dtype=np.uint8)
        else:
            self._state = CameraState.DEGRADED
            return False, None

    def get_metadata(self) -> dict:
        return {"width": 10, "height": 10, "fps": 30.0}

def test_camera_connect_success():
    cam = MockCamera("mock-1")
    assert cam.state == CameraState.DISCONNECTED
    assert cam.connect() is True
    assert cam.state == CameraState.CONNECTED
    assert cam.is_connected() is True

def test_camera_connect_fail():
    cam = MockCamera("mock-2", succeed_connect=False)
    assert cam.connect() is False
    assert cam.state == CameraState.ERROR
    assert cam.is_connected() is False

def test_camera_read_success():
    cam = MockCamera("mock-1")
    cam.connect()
    success, frame = cam.read()
    assert success is True
    assert frame is not None
    assert frame.shape == (10, 10, 3)
    assert cam.state == CameraState.STREAMING

def test_camera_disconnect():
    cam = MockCamera("mock-1")
    cam.connect()
    assert cam.is_connected() is True
    cam.disconnect()
    assert cam.is_connected() is False
    assert cam.state == CameraState.DISCONNECTED

def test_camera_read_fail():
    cam = MockCamera("mock-1", return_frame=False)
    cam.connect()
    success, frame = cam.read()
    assert success is False
    assert frame is None
    assert cam.state == CameraState.DEGRADED
