import time
import numpy as np
from typing import Optional
from app.models.status import DetectionResult

class BasicDetector:
    def __init__(self):
        # In a real scenario, we might initialize an OpenCV model or simple heuristics here
        pass

    def detect(self, frame: np.ndarray) -> Optional[DetectionResult]:
        """
        Performs basic detection.
        For Phase 1, this just proves the pipeline works by returning a mock result 
        if the frame is valid.
        """
        if frame is None:
            return None
            
        h, w = frame.shape[:2]
        
        # Phase 1: Return a simple dummy detection indicating the frame was processed
        return DetectionResult(
            label="pipeline_test",
            confidence=1.0,
            bounding_box=[w * 0.1, h * 0.1, w * 0.8, h * 0.8], # Center 80% box
            timestamp=time.time()
        )
