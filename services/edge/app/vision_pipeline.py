import time
import logging
import cv2
import numpy as np
from typing import Tuple

from app.config.settings import Settings
from app.detection.yolo import YOLODetector
from app.tracking.norfair_tracker import NorfairTracker
from app.zones.engine import ZoneEngine
from app.observations.emitter import ObservationEmitter

logger = logging.getLogger("vision")

class VisionPipeline:
    def __init__(self, config: Settings):
        self.config = config
        self.detector = YOLODetector(config.vision)
        self.tracker = NorfairTracker(config.vision.tracking)
        self.zone_engine = ZoneEngine(config.zones)
        self.emitter = ObservationEmitter()

        self.last_latency = 0.0

    def start(self):
        logger.info("Starting Vision Pipeline...")
        self.detector.load()

    def stop(self):
        logger.info("Stopping Vision Pipeline...")
        self.detector.unload()

    def process(self, frame: np.ndarray) -> Tuple[list, list, list]:
        """
        Processes a single frame.
        Returns:
            (detections, tracked_objects, observations)
        """
        start_time = time.time()
        
        # 1. Detection
        detections = self.detector.detect(frame)
        
        # 2. Tracking
        tracked_objects = self.tracker.update(detections)
        
        # 3. Zone Assignment
        self.zone_engine.assign_zones(tracked_objects)
        
        # 4. Observations
        observations = self.emitter.generate_observations(detections, tracked_objects)

        end_time = time.time()
        self.last_latency = (end_time - start_time) * 1000 # in ms

        return detections, tracked_objects, observations

    def get_health_metrics(self):
        return {
            "detector_status": self.detector.status,
            "model_loaded": self.detector.status == "READY",
            "tracker_status": self.tracker.status,
            "inference_latency_ms": self.last_latency,
            "active_track_count": self.tracker.active_track_count
        }

    def render_debug(self, frame: np.ndarray, tracked_objects: list, fps: dict) -> np.ndarray:
        """Draws debug visualization on the frame."""
        debug_frame = frame.copy()
        
        # Draw Zones
        for zone_id, zone_data in self.zone_engine.zones.items():
            pts = zone_data["polygon"]
            cv2.polylines(debug_frame, [pts], isClosed=True, color=(0, 255, 0), thickness=2)
            # Add Zone Name
            M = cv2.moments(pts)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                cv2.putText(debug_frame, zone_data["name"], (cx - 20, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
        # Draw Tracked Objects
        for obj in tracked_objects:
            x1, y1, x2, y2 = map(int, obj.bounding_box)
            cv2.rectangle(debug_frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
            label = f"{obj.label} #{obj.track_id} ({obj.current_zone or 'none'})"
            cv2.putText(debug_frame, label, (x1, max(0, y1 - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
            # Draw center
            cv2.circle(debug_frame, (int(obj.center['x']), int(obj.center['y'])), 4, (0, 0, 255), -1)

        # Draw FPS and Latency
        info = [
            f"Input: {fps.get('input_fps', 0)} FPS",
            f"Process: {fps.get('processing_fps', 0)} FPS",
            f"Inference: {fps.get('inference_fps', 0)} FPS",
            f"Latency: {self.last_latency:.1f} ms"
        ]
        for i, text in enumerate(info):
            cv2.putText(debug_frame, text, (10, 30 + i * 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        return debug_frame
