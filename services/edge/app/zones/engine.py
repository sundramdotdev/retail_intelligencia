import cv2
import numpy as np
from typing import List, Dict, Optional
from app.config.settings import ZoneConfig
from app.models.vision import TrackedObject

class ZoneEngine:
    def __init__(self, zone_configs: List[ZoneConfig]):
        self.zones = {}
        for zc in zone_configs:
            if zc.enabled:
                # Store polygons as numpy arrays for cv2
                pts = np.array(zc.polygon, np.int32)
                pts = pts.reshape((-1, 1, 2))
                self.zones[zc.id] = {
                    "name": zc.name,
                    "polygon": pts
                }

    def get_zone_for_point(self, x: float, y: float) -> Optional[str]:
        """Return the zone ID that contains the point (x, y)."""
        point = (float(x), float(y))
        
        for zone_id, zone_data in self.zones.items():
            # cv2.pointPolygonTest returns:
            # +1 if point is inside
            # 0 if point is on the contour
            # -1 if point is outside
            dist = cv2.pointPolygonTest(zone_data["polygon"], point, measureDist=False)
            if dist >= 0:
                return zone_id
                
        return None

    def assign_zones(self, tracked_objects: List[TrackedObject]) -> None:
        """Assign current_zone to tracked objects in-place."""
        for obj in tracked_objects:
            zone_id = self.get_zone_for_point(obj.center["x"], obj.center["y"])
            obj.current_zone = zone_id
