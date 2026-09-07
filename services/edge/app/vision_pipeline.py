"""
Vision Pipeline — Core edge AI processing pipeline.

Integrates: Detection → Tracking → Zone Assignment → Analytics → Observations.

Analytics subsystems integrated here:
  - PersonCounter    : peopleNow (active tracked persons)
  - FootfallCounter  : entriesToday (entrance crossing events)
  - ObjectAnalytics  : active object counts by COCO class
  - DwellTracker     : per-zone dwell times and zone occupancy
"""
import time
import logging
import cv2
import numpy as np
from typing import Optional, Tuple

from app.config.settings import Settings
from app.detection.yolo import YOLODetector
from app.tracking.norfair_tracker import NorfairTracker
from app.zones.engine import ZoneEngine
from app.observations.emitter import ObservationEmitter
from app.analytics.footfall import FootfallCounter
from app.analytics.person_count import PersonCounter
from app.analytics.object_analytics import ObjectAnalytics
from app.analytics.dwell_tracker import DwellTracker

logger = logging.getLogger("vision")


class VisionPipeline:
    def __init__(self, config: Settings):
        self.config = config
        self.detector = YOLODetector(config.vision)
        self.tracker = NorfairTracker(config.vision.tracking)
        self.zone_engine = ZoneEngine(config.zones)
        self.emitter = ObservationEmitter()

        # ── Analytics Subsystems ──────────────────────────────────────────
        entrance_zone_id = getattr(config, "entrance_zone_id", None) or "zone-entrance"
        self.person_counter = PersonCounter()
        self.footfall_counter = FootfallCounter(entrance_zone_id=entrance_zone_id)
        self.object_analytics = ObjectAnalytics()
        self.dwell_tracker = DwellTracker()
        # ─────────────────────────────────────────────────────────────────

        self.last_latency = 0.0
        self._analytics_snapshot: dict = {}

    def start(self):
        logger.info("Starting Vision Pipeline...")
        self.detector.load()

    def stop(self):
        logger.info("Stopping Vision Pipeline...")
        self.detector.unload()

    def process(self, frame: np.ndarray) -> Tuple[list, list, list]:
        """
        Processes a single frame through the full pipeline.

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

        # 4. Analytics subsystems (order matters for zone context)
        people_now = self.person_counter.count(tracked_objects)
        footfall_events = self.footfall_counter.update(tracked_objects)
        obj_counts = self.object_analytics.compute(tracked_objects)
        dwell_completed = self.dwell_tracker.update(tracked_objects)

        # 5. Observations (zone transitions, new track events)
        observations = self.emitter.generate_observations(detections, tracked_objects)

        end_time = time.time()
        self.last_latency = (end_time - start_time) * 1000  # ms

        # 6. Update analytics snapshot
        footfall_snap = self.footfall_counter.get_snapshot()
        dwell_snap = self.dwell_tracker.get_snapshot()
        self._analytics_snapshot = {
            "peopleNow": people_now,
            "footfallToday": footfall_snap["entriesToday"],
            "footfallLastHour": footfall_snap["entriesLastHour"],
            "footfallLast15Min": footfall_snap["entriesLast15Min"],
            "averageDwellSeconds": dwell_snap["globalAverageDwellSeconds"],
            "longestDwellSeconds": dwell_snap["globalLongestDwellSeconds"],
            "activeObjects": sum(obj_counts.values()),
            "objectsByClass": obj_counts,
            "zoneOccupancy": dwell_snap["zoneOccupancy"],
            "dwellByZone": dwell_snap["byZone"],
        }

        return detections, tracked_objects, observations

    def get_analytics_snapshot(self) -> dict:
        """Return the latest analytics computed in the most recent process() call."""
        return dict(self._analytics_snapshot)

    def get_model_metadata(self) -> dict:
        """Return YOLO model metadata for dashboard display."""
        class_names = {}
        if self.detector.model and hasattr(self.detector, "_class_names"):
            class_names = self.detector._class_names
        return {
            "model": self.config.vision.detector.model,
            "dataset": "COCO",
            "classCount": len(class_names),
            "classes": list(class_names.values()) if class_names else [],
            "device": self.config.vision.detector.device,
            "status": self.detector.status,
        }

    def get_health_metrics(self):
        return {
            "detector_status": self.detector.status,
            "model_loaded": self.detector.status == "READY",
            "tracker_status": self.tracker.status,
            "inference_latency_ms": self.last_latency,
            "active_track_count": self.tracker.active_track_count,
        }

    def render_debug(self, frame: np.ndarray, tracked_objects: list, fps: dict) -> np.ndarray:
        """Draws debug visualization on the frame."""
        debug_frame = frame.copy()

        # Draw Zones
        for zone_id, zone_data in self.zone_engine.zones.items():
            pts = zone_data["polygon"]
            color = (0, 200, 100)  # Green for regular zones
            if zone_id == self.footfall_counter.entrance_zone_id:
                color = (0, 140, 255)  # Orange for entrance zone
            cv2.polylines(debug_frame, [pts], isClosed=True, color=color, thickness=2)
            M = cv2.moments(pts)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                cv2.putText(debug_frame, zone_data["name"], (cx - 20, cy),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # Draw Tracked Objects
        for obj in tracked_objects:
            x1, y1, x2, y2 = map(int, obj.bounding_box)
            is_person = obj.label.lower() == "person"
            color = (0, 120, 255) if is_person else (200, 200, 0)
            cv2.rectangle(debug_frame, (x1, y1), (x2, y2), color, 2)

            # Label: class + track_id + confidence
            label_text = f"{obj.label} #{obj.track_id} {obj.confidence:.2f}"
            label_bg_y = max(0, y1 - 24)
            cv2.rectangle(debug_frame, (x1, label_bg_y), (x1 + len(label_text) * 8, y1), color, -1)
            cv2.putText(debug_frame, label_text, (x1 + 2, y1 - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)

            # Zone label below bbox
            if obj.current_zone:
                zone_name = self.zone_engine.zones.get(obj.current_zone, {}).get("name", obj.current_zone)
                cv2.putText(debug_frame, zone_name, (x1, y2 + 16),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)

            cv2.circle(debug_frame, (int(obj.center["x"]), int(obj.center["y"])), 3, (0, 0, 255), -1)

        # Draw HUD overlay (top-left)
        snap = self._analytics_snapshot
        hud_lines = [
            f"Input: {fps.get('input_fps', 0):.1f} FPS",
            f"Inference: {fps.get('inference_fps', 0):.1f} FPS  Lat: {self.last_latency:.0f}ms",
            f"People: {snap.get('peopleNow', 0)}   Footfall: {snap.get('footfallToday', 0)}",
            f"Objects: {snap.get('activeObjects', 0)}",
        ]
        for i, line in enumerate(hud_lines):
            y_pos = 22 + i * 22
            cv2.putText(debug_frame, line, (10, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 220, 220), 1)

        return debug_frame
