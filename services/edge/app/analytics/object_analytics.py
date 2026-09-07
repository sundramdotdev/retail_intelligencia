"""
Object Analytics — Active Object Counts by COCO Class.

Computes the number of currently visible tracked objects grouped by their
COCO class label. Uses active tracks only — not cumulative totals.

Two distinct concepts exposed:
  activeByClass   : {label: count} for all tracked objects in current frame
  activeTotal     : total across all classes
  personCount     : shortcut for class "person"

Note:
  This system uses YOLO11n with the COCO pretrained dataset.
  It can detect general COCO classes (person, bottle, cup, backpack, chair, etc.).
  It does NOT detect retail SKUs, product names, or brand names.
  Retail product detection requires a custom-trained model (future phase).
"""
import logging
from collections import defaultdict
from typing import Dict, List

from app.models.vision import TrackedObject

logger = logging.getLogger("analytics.objects")


class ObjectAnalytics:
    """Computes per-class active object counts from current tracked objects."""

    def __init__(self):
        self._last_snapshot: Dict[str, int] = {}

    def compute(self, tracked_objects: List[TrackedObject]) -> Dict[str, int]:
        """
        Count currently tracked objects by COCO class label.

        Args:
            tracked_objects: Current frame tracked objects.

        Returns:
            Dict mapping class label → active count.
            Example: {"person": 4, "bottle": 2, "cup": 1, "backpack": 3}
        """
        counts: Dict[str, int] = defaultdict(int)
        for obj in tracked_objects:
            counts[obj.label.lower()] += 1

        snapshot = dict(counts)
        self._last_snapshot = snapshot
        return snapshot

    def get_snapshot(self) -> Dict:
        """Return the last computed analytics snapshot."""
        counts = self._last_snapshot
        total = sum(counts.values())
        person_count = counts.get("person", 0)
        return {
            "activeByClass": counts,
            "activeTotal": total,
            "personCount": person_count,
        }

    @property
    def last_snapshot(self) -> Dict[str, int]:
        return self._last_snapshot
