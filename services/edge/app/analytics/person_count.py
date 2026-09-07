"""
Person Counter — Active Person Count from Tracked Objects.

Definition:
  peopleNow = number of CURRENTLY ACTIVE tracked objects whose label == 'person'
              in the current frame.

This is NOT a cumulative sum of all person detections ever seen.
It reflects the live headcount visible to the camera right now.

Frame 1: tracks [person#1, person#2, person#3] → peopleNow = 3
Frame 2: tracks [person#1, person#2, person#3] → peopleNow = 3  (NOT 6)
Frame 3: person#1 leaves → tracks [person#2, person#3] → peopleNow = 2
"""
import logging
from typing import List

from app.models.vision import TrackedObject

logger = logging.getLogger("analytics.person_count")


class PersonCounter:
    """Computes the current active person count from tracked objects."""

    def __init__(self, person_label: str = "person"):
        self.person_label = person_label.lower()
        self._last_count: int = 0

    def count(self, tracked_objects: List[TrackedObject]) -> int:
        """
        Count actively tracked persons in the current frame.

        Args:
            tracked_objects: The list of TrackedObject from the current tracker update.

        Returns:
            Integer count of currently visible/tracked people.
        """
        count = sum(
            1
            for obj in tracked_objects
            if obj.label.lower() == self.person_label
        )
        if count != self._last_count:
            logger.debug(f"[PERSON_COUNT] People now: {count} (was {self._last_count})")
        self._last_count = count
        return count

    @property
    def last_count(self) -> int:
        """Returns the most recently computed person count."""
        return self._last_count
