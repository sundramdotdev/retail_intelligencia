import cv2
from typing import Tuple, Optional
import numpy as np
from app.camera.base import CameraSource
from app.models.status import CameraState
import logging

logger = logging.getLogger("camera")

class RTSPCamera(CameraSource):
    def __init__(self, camera_id: str, url: str):
        super().__init__(camera_id)
        self.url = url
        self.cap = None

    def connect(self) -> bool:
        self._state = CameraState.CONNECTING
        # Do not log full URL if it might contain credentials, but for now we assume safe logging or stripped URL
        safe_url = self.url.split('@')[-1] if '@' in self.url else self.url
        logger.info(f"[{self.camera_id}] Connecting to RTSP camera at {safe_url}")
        
        self.cap = cv2.VideoCapture(self.url, cv2.CAP_FFMPEG)
        
        if self.cap.isOpened():
            self._state = CameraState.CONNECTED
            logger.info(f"[{self.camera_id}] Connected successfully")
            return True
        else:
            self._state = CameraState.ERROR
            logger.error(f"[{self.camera_id}] Failed to connect")
            return False

    def disconnect(self) -> None:
        logger.info(f"[{self.camera_id}] Disconnecting")
        if self.cap:
            self.cap.release()
            self.cap = None
        self._state = CameraState.DISCONNECTED

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        if not self.is_connected() or not self.cap:
            return False, None

        ret, frame = self.cap.read()
        if ret:
            self._state = CameraState.STREAMING
            return True, frame
        else:
            logger.warning(f"[{self.camera_id}] Frame read failed")
            self._state = CameraState.DEGRADED
            return False, None

    def get_metadata(self) -> dict:
        if not self.cap or not self.cap.isOpened():
            return {}
        
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        
        return {
            "width": width,
            "height": height,
            "fps": fps
        }
