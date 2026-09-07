"""
Dwell Tracker — Per-Track, Per-Zone Dwell Time Measurement.

Measures how long each tracked object spends inside each zone.

Lifecycle:
  1. Track enters zone   → record enteredAt timestamp
  2. Track stays in zone → compute running dwell
  3. Track exits zone    → finalize dwell observation, update zone averages
  4. Track is lost       → finalize any open dwell observations

Outputs:
  - Completed dwell observations (per track/zone pair)
  - Rolling zone-level average dwell seconds
  - Longest dwell observed per zone (in current session)

Zone Occupancy (distinct from dwell):
  zone_occupancy = {zone_id: count_of_active_persons_in_zone}
  This is computed each frame from current tracked persons.
"""
import logging
import time
from collections import defaultdict
from typing import Dict, List, Optional, Tuple

from app.models.vision import TrackedObject

logger = logging.getLogger("analytics.dwell")


class DwellObservation:
    """A completed dwell time record for one track in one zone."""
    __slots__ = ("track_id", "label", "zone_id", "entered_at", "exited_at", "dwell_seconds")

    def __init__(self, track_id: int, label: str, zone_id: str, entered_at: float, exited_at: float):
        self.track_id = track_id
        self.label = label
        self.zone_id = zone_id
        self.entered_at = entered_at
        self.exited_at = exited_at
        self.dwell_seconds = exited_at - entered_at

    def to_dict(self) -> Dict:
        return {
            "trackId": self.track_id,
            "label": self.label,
            "zoneId": self.zone_id,
            "dwellSeconds": round(self.dwell_seconds, 1),
        }


class DwellTracker:
    """
    Tracks per-track, per-zone dwell times and computes zone-level aggregates.
    """

    # Rolling window for average dwell computation (number of recent observations)
    _AVERAGE_WINDOW = 20

    def __init__(self):
        # (track_id, zone_id) → entered_at timestamp
        self._active: Dict[Tuple[int, str], float] = {}

        # Per-track current zone label (to detect zone transitions)
        self._track_zones: Dict[int, Optional[str]] = {}
        self._track_labels: Dict[int, str] = {}

        # Completed observations per zone (ring buffer of last N)
        self._zone_observations: Dict[str, List[float]] = defaultdict(list)

        # Longest dwell per zone (session)
        self._zone_longest: Dict[str, float] = {}

        # Zone occupancy (persons per zone, current frame)
        self._zone_occupancy: Dict[str, int] = {}

    def update(self, tracked_objects: List[TrackedObject]) -> List[DwellObservation]:
        """
        Process the current frame's tracked objects.

        Returns completed DwellObservation records for tracks that exited zones.
        """
        now = time.time()
        current_tracks: Dict[int, Optional[str]] = {}
        completed: List[DwellObservation] = []

        # Compute zone occupancy for this frame (person-only)
        occupancy: Dict[str, int] = defaultdict(int)

        for obj in tracked_objects:
            tid = obj.track_id
            current_zone = obj.current_zone
            current_tracks[tid] = current_zone
            self._track_labels[tid] = obj.label

            if current_zone and obj.label.lower() == "person":
                occupancy[current_zone] += 1

        self._zone_occupancy = dict(occupancy)

        # Process zone transitions
        for tid, new_zone in current_tracks.items():
            old_zone = self._track_zones.get(tid)
            label = self._track_labels.get(tid, "unknown")

            if old_zone != new_zone:
                # Finalize old zone dwell
                if old_zone is not None:
                    key = (tid, old_zone)
                    entered_at = self._active.pop(key, None)
                    if entered_at is not None:
                        obs = DwellObservation(tid, label, old_zone, entered_at, now)
                        completed.append(obs)
                        self._record_observation(old_zone, obs.dwell_seconds)
                        logger.debug(
                            f"[DWELL] Track #{tid} ({label}) left {old_zone} "
                            f"after {obs.dwell_seconds:.1f}s"
                        )

                # Start new zone dwell
                if new_zone is not None:
                    self._active[(tid, new_zone)] = now

            self._track_zones[tid] = new_zone

        # Handle lost tracks
        lost_ids = set(self._track_zones.keys()) - set(current_tracks.keys())
        for tid in lost_ids:
            old_zone = self._track_zones.get(tid)
            label = self._track_labels.get(tid, "unknown")
            if old_zone is not None:
                key = (tid, old_zone)
                entered_at = self._active.pop(key, None)
                if entered_at is not None:
                    obs = DwellObservation(tid, label, old_zone, entered_at, now)
                    completed.append(obs)
                    self._record_observation(old_zone, obs.dwell_seconds)
                    logger.debug(
                        f"[DWELL] Track #{tid} lost in {old_zone} "
                        f"after {obs.dwell_seconds:.1f}s"
                    )
            self._track_zones.pop(tid, None)
            self._track_labels.pop(tid, None)

        return completed

    def _record_observation(self, zone_id: str, dwell_seconds: float) -> None:
        """Record a completed dwell observation into zone aggregates."""
        obs_list = self._zone_observations[zone_id]
        obs_list.append(dwell_seconds)
        # Keep only the last N observations
        if len(obs_list) > self._AVERAGE_WINDOW:
            self._zone_observations[zone_id] = obs_list[-self._AVERAGE_WINDOW:]

        # Update longest
        current_longest = self._zone_longest.get(zone_id, 0.0)
        if dwell_seconds > current_longest:
            self._zone_longest[zone_id] = dwell_seconds

    def get_zone_average(self, zone_id: str) -> float:
        """Average dwell seconds for the given zone (recent observations)."""
        obs = self._zone_observations.get(zone_id, [])
        return round(sum(obs) / len(obs), 1) if obs else 0.0

    def get_zone_longest(self, zone_id: str) -> float:
        """Longest dwell seconds ever seen for the given zone in this session."""
        return round(self._zone_longest.get(zone_id, 0.0), 1)

    def get_current_dwell(self, track_id: int, zone_id: str) -> float:
        """Running dwell for an active (not yet completed) track in a zone."""
        key = (track_id, zone_id)
        entered_at = self._active.get(key)
        return round(time.time() - entered_at, 1) if entered_at else 0.0

    def get_zone_occupancy(self) -> Dict[str, int]:
        """Current person count per zone from the last update."""
        return dict(self._zone_occupancy)

    def get_snapshot(self) -> Dict:
        """Full analytics snapshot for all zones."""
        zone_ids = set(self._zone_observations.keys()) | set(self._zone_longest.keys())
        zones = {}
        for zid in zone_ids:
            zones[zid] = {
                "averageDwellSeconds": self.get_zone_average(zid),
                "longestDwellSeconds": self.get_zone_longest(zid),
            }

        # Global averages across all observations
        all_obs = [d for obs in self._zone_observations.values() for d in obs]
        global_avg = round(sum(all_obs) / len(all_obs), 1) if all_obs else 0.0
        global_max = max(all_obs) if all_obs else 0.0

        return {
            "globalAverageDwellSeconds": global_avg,
            "globalLongestDwellSeconds": round(global_max, 1),
            "byZone": zones,
            "zoneOccupancy": self.get_zone_occupancy(),
        }
