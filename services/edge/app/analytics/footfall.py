"""
Footfall Counter — Entrance Crossing Detection.

Implements crossing-based footfall tracking:
  - A person must cross from OUTSIDE → INSIDE an entrance zone to count as an ENTRY.
  - Debounce: a track_id that is already inside cannot trigger a second entry
    until it has been seen OUTSIDE again (full exit + re-entry cycle required).
  - Double-count prevention: per-track crossing state machine.

Footfall ≠ Person Count.
  - People Now  = number of actively tracked person objects this frame
  - Footfall    = cumulative count of distinct entrance crossing events

Persistence: counts reset on process restart unless persisted to the Event buffer
(which is the role of the Retail Intelligence Engine + backend).
"""
import logging
import time
from collections import defaultdict
from datetime import datetime, timezone
from threading import Lock
from typing import Dict, List, Optional, Set

from app.models.vision import TrackedObject

logger = logging.getLogger("analytics.footfall")


class FootfallCounter:
    """
    Counts person entries through a designated entrance zone.

    State per track_id:
      UNKNOWN   — track first seen, zone membership unknown
      OUTSIDE   — currently outside the entrance zone
      INSIDE    — currently inside the entrance zone (entry already counted)

    A new ENTRY is counted only on OUTSIDE → INSIDE transition.
    """

    # Crossing state constants
    STATE_UNKNOWN = "UNKNOWN"
    STATE_OUTSIDE = "OUTSIDE"
    STATE_INSIDE = "INSIDE"

    def __init__(self, entrance_zone_id: str, person_label: str = "person"):
        """
        Args:
            entrance_zone_id: The zone ID that represents the entrance/entry point.
            person_label:     The COCO class label for people (default: 'person').
        """
        self.entrance_zone_id = entrance_zone_id
        self.person_label = person_label.lower()

        self._lock = Lock()

        # Per-track crossing state
        self._track_states: Dict[int, str] = {}

        # Footfall counters
        self._entries_total: int = 0
        self._exits_total: int = 0
        self._session_start: float = time.time()

        # Time-windowed entry tracking: list of Unix timestamps
        self._entry_timestamps: List[float] = []

        # Set of currently-inside track IDs (for person-now in entrance zone)
        self._inside_tracks: Set[int] = set()

    def update(self, tracked_objects: List[TrackedObject]) -> List[Dict]:
        """
        Process current frame tracked objects.

        Returns a list of crossing events observed this frame:
          [{"type": "ENTRY", "track_id": 17, "timestamp": ...}, ...]
        """
        events = []
        current_time = time.time()
        current_person_ids = set()

        with self._lock:
            for obj in tracked_objects:
                if obj.label.lower() != self.person_label:
                    continue

                tid = obj.track_id
                current_person_ids.add(tid)
                in_entrance = obj.current_zone == self.entrance_zone_id

                prev_state = self._track_states.get(tid, self.STATE_UNKNOWN)

                if prev_state == self.STATE_UNKNOWN:
                    # First time we see this track — set state without counting
                    new_state = self.STATE_INSIDE if in_entrance else self.STATE_OUTSIDE

                elif prev_state == self.STATE_OUTSIDE and in_entrance:
                    # Crossing: OUTSIDE → INSIDE = ENTRY
                    new_state = self.STATE_INSIDE
                    self._entries_total += 1
                    self._entry_timestamps.append(current_time)
                    self._inside_tracks.add(tid)
                    events.append({
                        "type": "ENTRY",
                        "track_id": tid,
                        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    })
                    logger.info(f"[FOOTFALL] ENTRY — Track #{tid} crossed into {self.entrance_zone_id} "
                                f"| Total today: {self._entries_total}")

                elif prev_state == self.STATE_INSIDE and not in_entrance:
                    # INSIDE → OUTSIDE = EXIT
                    new_state = self.STATE_OUTSIDE
                    self._exits_total += 1
                    self._inside_tracks.discard(tid)
                    events.append({
                        "type": "EXIT",
                        "track_id": tid,
                        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                    })
                    logger.debug(f"[FOOTFALL] EXIT — Track #{tid} left {self.entrance_zone_id}")

                else:
                    # State unchanged
                    new_state = prev_state
                    if in_entrance:
                        self._inside_tracks.add(tid)

                self._track_states[tid] = new_state

            # Cleanup lost tracks
            lost_ids = set(self._track_states.keys()) - current_person_ids
            for tid in lost_ids:
                self._track_states.pop(tid, None)
                self._inside_tracks.discard(tid)

            # Trim old timestamps
            self._prune_old_timestamps(current_time)

        return events

    def _prune_old_timestamps(self, now: float) -> None:
        """Remove timestamps older than 1 hour from the rolling window."""
        cutoff = now - 3600
        self._entry_timestamps = [t for t in self._entry_timestamps if t >= cutoff]

    def get_snapshot(self) -> Dict:
        """Return current footfall metrics snapshot."""
        now = time.time()
        with self._lock:
            self._prune_old_timestamps(now)
            entries_last_hour = sum(1 for t in self._entry_timestamps if t >= now - 3600)
            entries_last_15min = sum(1 for t in self._entry_timestamps if t >= now - 900)
            return {
                "entriesToday": self._entries_total,
                "exitsToday": self._exits_total,
                "entriesLastHour": entries_last_hour,
                "entriesLast15Min": entries_last_15min,
                "currentlyInEntrance": len(self._inside_tracks),
            }

    def reset_daily(self) -> None:
        """Reset daily counters. Call at store open or midnight."""
        with self._lock:
            self._entries_total = 0
            self._exits_total = 0
            self._session_start = time.time()
            logger.info("[FOOTFALL] Daily counters reset.")
