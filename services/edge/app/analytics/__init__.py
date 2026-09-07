"""
Edge Analytics Subsystems for Retail Intelligencia.

Provides real-time operational analytics computed from tracked object data:
  - FootfallCounter   : Entrance crossing detection with debounce
  - PersonCounter     : Active person count from current tracked objects
  - ObjectAnalytics   : Per-class active object counts
  - DwellTracker      : Per-track, per-zone dwell time measurement
"""
from .footfall import FootfallCounter
from .person_count import PersonCounter
from .object_analytics import ObjectAnalytics
from .dwell_tracker import DwellTracker

__all__ = [
    "FootfallCounter",
    "PersonCounter",
    "ObjectAnalytics",
    "DwellTracker",
]
