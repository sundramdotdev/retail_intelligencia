import time
import logging
from typing import List, Optional
import numpy as np

from app.detection.base import Detector
from app.models.vision import Detection
from app.config.settings import VisionConfig

logger = logging.getLogger("detector")

class YOLODetector(Detector):
    def __init__(self, config: VisionConfig):
        self.config = config.detector
        self.classes_config = config.classes
        self.model = None
        self._status = "NOT_INITIALIZED"
        self._device = self.config.device
        self._class_names = {}
        self._filtered_classes = set()

    def load(self) -> bool:
        self._status = "LOADING"
        logger.info(f"Loading YOLO model from {self.config.model} on device {self._device}")
        
        try:
            # We import ultralytics here so it doesn't break if not installed
            from ultralytics import YOLO
            
            # YOLO automatically handles downloading if the model is a known preset like yolo11n.pt
            # and it caches it locally.
            self.model = YOLO(self.config.model)
            
            # Extract class names mapping (id -> name)
            self._class_names = self.model.names
            
            # Validate requested classes against model's classes
            requested = [c.lower() for c in self.classes_config.enabled]
            for class_id, class_name in self._class_names.items():
                if class_name.lower() in requested:
                    self._filtered_classes.add(class_id)
            
            # Check if any requested classes were not found
            model_class_names = [name.lower() for name in self._class_names.values()]
            for req in requested:
                if req not in model_class_names:
                    logger.warning(f"Configured class '{req}' is not supported by model {self.config.model}")

            self._status = "READY"
            logger.info(f"Model loaded successfully. Tracking {len(self._filtered_classes)} classes.")
            return True
            
        except Exception as e:
            self._status = "ERROR"
            logger.error(f"Failed to load YOLO model: {e}")
            return False

    def detect(self, frame: np.ndarray) -> List[Detection]:
        if self._status != "READY" or self.model is None:
            return []

        if frame is None or frame.size == 0:
            return []

        try:
            # Run inference
            # device=None will use auto/ultralytics default unless explicitly passed
            device_arg = None if self._device == "auto" else self._device
            
            results = self.model(
                frame, 
                conf=self.config.confidence_threshold,
                iou=self.config.iou_threshold,
                device=device_arg,
                verbose=False
            )
            
            detections = []
            timestamp = time.time()
            
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    class_id = int(box.cls[0].item())
                    
                    if self._filtered_classes and class_id not in self._filtered_classes:
                        continue
                        
                    conf = float(box.conf[0].item())
                    xyxy = box.xyxy[0].tolist()  # [x1, y1, x2, y2]
                    
                    label = self._class_names.get(class_id, "unknown")
                    
                    detections.append(Detection(
                        class_id=class_id,
                        label=label,
                        confidence=conf,
                        bounding_box=xyxy,
                        timestamp=timestamp
                    ))
                    
            return detections

        except Exception as e:
            logger.error(f"Inference error: {e}")
            self._status = "DEGRADED"
            return []

    def unload(self) -> None:
        self.model = None
        self._status = "STOPPED"
        logger.info("YOLO model unloaded.")

    @property
    def status(self) -> str:
        return self._status
