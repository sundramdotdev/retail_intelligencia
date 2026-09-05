import cv2
import numpy as np
from typing import Optional

def resize_frame(frame: np.ndarray, target_width: int, target_height: int) -> np.ndarray:
    """Resize the frame to the target dimensions if necessary."""
    if frame is None:
        return None
    h, w = frame.shape[:2]
    if w != target_width or h != target_height:
        return cv2.resize(frame, (target_width, target_height))
    return frame

def validate_frame(frame: np.ndarray) -> bool:
    """Validate that the frame is usable (e.g., not completely empty/corrupt)."""
    if frame is None or frame.size == 0:
        return False
    # Simple check for corrupted frames could be added here
    return True
