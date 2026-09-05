import time
import logging
from typing import Optional, Tuple
import numpy as np

from app.camera.base import CameraSource
from app.config.settings import Settings

logger = logging.getLogger("stream")

class VideoStreamManager:
    def __init__(self, camera: CameraSource, config: Settings):
        self.camera = camera
        self.config = config
        self.target_fps = config.processing.target_fps
        self.frame_interval = 1.0 / self.target_fps if self.target_fps > 0 else 0
        
        self.last_processed_time = 0.0
        self.reconnect_delay = 5.0  # seconds

    def connect(self) -> bool:
        return self.camera.connect()

    def disconnect(self) -> None:
        self.camera.disconnect()

    def read_and_sample(self) -> Tuple[bool, Optional[np.ndarray], bool]:
        """
        Reads a frame from the camera and determines if it should be processed based on target FPS.
        Returns:
            (success, frame, should_process)
        """
        success, frame = self.camera.read()
        
        if not success:
            return False, None, False

        current_time = time.time()
        should_process = False

        if current_time - self.last_processed_time >= self.frame_interval:
            should_process = True
            self.last_processed_time = current_time

        return True, frame, should_process

    def handle_reconnect(self):
        """Attempts to reconnect the camera with a backoff delay."""
        logger.warning(f"[{self.camera.camera_id}] Attempting to reconnect in {self.reconnect_delay} seconds...")
        time.sleep(self.reconnect_delay)
        return self.connect()
