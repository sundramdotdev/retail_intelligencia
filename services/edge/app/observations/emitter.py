import time
import logging
from typing import List, Dict, Tuple
from app.models.vision import Detection, TrackedObject, Observation

logger = logging.getLogger("observations")

class ObservationEmitter:
    def __init__(self):
        # track_id -> zone_id
        self.previous_zones: Dict[int, str] = {}
        # We also might want to track which objects we've already emitted PERSON_DETECTED for
        self.known_tracks = set()

    def generate_observations(self, detections: List[Detection], tracked_objects: List[TrackedObject]) -> List[Observation]:
        observations = []
        current_time = time.time()
        
        # We can emit generic detection observations if needed, but usually tracked objects are better
        # For Phase 2, we emit PERSON_DETECTED or OBJECT_DETECTED once per new track
        
        current_track_ids = set()
        
        for obj in tracked_objects:
            current_track_ids.add(obj.track_id)
            
            # 1. New Object Detected
            if obj.track_id not in self.known_tracks:
                self.known_tracks.add(obj.track_id)
                obs_type = "PERSON_DETECTED" if obj.label.lower() == "person" else "OBJECT_DETECTED"
                obs = Observation(
                    type=obs_type,
                    track_id=obj.track_id,
                    timestamp=current_time,
                    metadata={"label": obj.label, "confidence": obj.confidence}
                )
                observations.append(obs)
                logger.info(f"[OBSERVATION] {obs_type}: Track #{obj.track_id} ({obj.label})")

            # 2. Zone Transitions
            prev_zone = self.previous_zones.get(obj.track_id)
            curr_zone = obj.current_zone
            
            if prev_zone != curr_zone:
                if prev_zone is None and curr_zone is not None:
                    # Entered a zone
                    obs = Observation(
                        type="ZONE_ENTERED",
                        track_id=obj.track_id,
                        zone_id=curr_zone,
                        timestamp=current_time
                    )
                    observations.append(obs)
                    logger.info(f"[OBSERVATION] ZONE_ENTERED: Track #{obj.track_id} -> {curr_zone}")
                    
                elif prev_zone is not None and curr_zone is None:
                    # Exited all zones
                    obs = Observation(
                        type="ZONE_EXITED",
                        track_id=obj.track_id,
                        zone_id=prev_zone,
                        timestamp=current_time
                    )
                    observations.append(obs)
                    logger.info(f"[OBSERVATION] ZONE_EXITED: Track #{obj.track_id} left {prev_zone}")
                    
                elif prev_zone is not None and curr_zone is not None:
                    # Changed zones
                    obs = Observation(
                        type="ZONE_CHANGED",
                        track_id=obj.track_id,
                        zone_id=curr_zone, # Destination zone
                        timestamp=current_time,
                        metadata={"from_zone": prev_zone}
                    )
                    observations.append(obs)
                    logger.info(f"[OBSERVATION] ZONE_CHANGED: Track #{obj.track_id}: {prev_zone} -> {curr_zone}")
                
                # Update previous zone state
                self.previous_zones[obj.track_id] = curr_zone
                
        # 3. Cleanup lost tracks
        lost_tracks = set(self.previous_zones.keys()) - current_track_ids
        for tid in lost_tracks:
            del self.previous_zones[tid]
            if tid in self.known_tracks:
                self.known_tracks.remove(tid)
                
        return observations
