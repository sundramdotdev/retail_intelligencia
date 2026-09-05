import time
import logging
import numpy as np
from typing import List, Dict, Any

from app.tracking.base import Tracker
from app.models.vision import Detection, TrackedObject
from app.config.settings import TrackingConfig

logger = logging.getLogger("tracker")

class NorfairTracker(Tracker):
    def __init__(self, config: TrackingConfig):
        self.config = config
        self._tracker = None
        self._status = "NOT_INITIALIZED"
        self._track_ages = {}
        
        try:
            from norfair import Tracker as NFTracker, Detection as NFDetection
            
            # Simple euclidean distance function for Norfair
            def euclidean_distance(detection: NFDetection, tracked_object: Any) -> float:
                return np.linalg.norm(detection.points - tracked_object.estimate)
                
            self.NFTracker = NFTracker
            self.NFDetection = NFDetection
            self.euclidean_distance = euclidean_distance
            
            # Initialize norfair tracker
            # max_lost is equivalent to max_lost_frames
            # hit_counter_max is frames before a track is considered "initialized"
            self._tracker = self.NFTracker(
                distance_function=self.euclidean_distance,
                distance_threshold=100.0, # pixel distance threshold
                initialization_delay=3,
                hit_counter_max=15,
                past_detections_length=5
            )
            self._status = "READY"
        except ImportError:
            logger.error("Norfair is not installed. Tracking will be disabled.")
            self._status = "ERROR"
        except Exception as e:
            logger.error(f"Failed to initialize NorfairTracker: {e}")
            self._status = "ERROR"

    def update(self, detections: List[Detection]) -> List[TrackedObject]:
        if self._status != "READY" or self._tracker is None:
            return []

        # Convert app Detections to norfair Detections
        # We'll track the center of the bounding box
        nf_detections = []
        for det in detections:
            x1, y1, x2, y2 = det.bounding_box
            cx = (x1 + x2) / 2.0
            cy = (y1 + y2) / 2.0
            points = np.array([[cx, cy]])
            
            # Pack our original detection in data
            nf_det = self.NFDetection(points, data=det)
            nf_detections.append(nf_det)

        # Update tracker
        try:
            tracked_objects = self._tracker.update(detections=nf_detections)
        except Exception as e:
            logger.error(f"Tracker update failed: {e}")
            return []

        # Convert back to our TrackedObject model
        results = []
        current_time = time.time()
        
        # Cleanup old ages
        current_ids = {obj.id for obj in tracked_objects}
        keys_to_remove = [tid for tid in self._track_ages if tid not in current_ids]
        for k in keys_to_remove:
            del self._track_ages[k]

        for obj in tracked_objects:
            # Norfair considers an object 'live' if it has been matched recently
            if not obj.live_points.any():
                continue

            track_id = obj.id
            
            if track_id not in self._track_ages:
                self._track_ages[track_id] = current_time
                
            first_seen = self._track_ages[track_id]
            age = int(obj.age)
            
            # Last detection data attached to the tracked object
            last_det = obj.last_detection.data if obj.last_detection else None
            
            if last_det:
                label = last_det.label
                confidence = last_det.confidence
                bbox = last_det.bounding_box
            else:
                # If we don't have the last detection (e.g., missed frame), 
                # we can approximate or skip. For now, we skip if we can't get bbox.
                continue
            
            est_cx, est_cy = obj.estimate[0]
            
            results.append(TrackedObject(
                track_id=track_id,
                label=label,
                confidence=confidence,
                bounding_box=bbox,
                center={"x": float(est_cx), "y": float(est_cy)},
                first_seen=first_seen,
                last_seen=current_time,
                age=age,
                current_zone=None
            ))
            
        return results

    @property
    def active_track_count(self) -> int:
        return len(self._track_ages) if self._status == "READY" else 0

    @property
    def status(self) -> str:
        return self._status
