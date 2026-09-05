from typing import Optional, Tuple
from app.intelligence.rules.base import RetailRule
from app.intelligence.context import RetailContext
from app.events.models import RetailEvent
from app.config.settings import ShelfZoneConfig, ZoneConfig
import logging

logger = logging.getLogger("rules.shelf")

class ShelfRule(RetailRule):
    def __init__(self, shelf_config: ShelfZoneConfig, all_zones: list[ZoneConfig], *args, **kwargs):
        super().__init__(name=f"ShelfRule_{shelf_config.id}", *args, **kwargs)
        self.shelf_config = shelf_config
        self.shelf_polygon = next((z.polygon for z in all_zones if z.id == shelf_config.id), None)
        
    def _calculate_polygon_area(self, poly: list[list[int]]) -> float:
        # Shoelace formula for area
        if not poly or len(poly) < 3: return 0.0
        x = [p[0] for p in poly]
        y = [p[1] for p in poly]
        return 0.5 * abs(sum(x[i]*y[i+1] - x[i+1]*y[i] for i in range(len(poly)-1)) + x[-1]*y[0] - x[0]*y[-1])

    def _calculate_box_area(self, box: list[float]) -> float:
        if len(box) != 4: return 0.0
        return max(0.0, box[2] - box[0]) * max(0.0, box[3] - box[1])

    def _get_pseudo_occupancy(self, context: RetailContext) -> float:
        if not self.shelf_polygon: return 1.0 # Safe default
        
        shelf_area = self._calculate_polygon_area(self.shelf_polygon)
        if shelf_area <= 0: return 1.0
        
        # Consider bottles and cups as "products"
        products = [t for t in context.tracks if t.label in ["bottle", "cup"] and t.current_zone == self.shelf_config.id]
        
        occupied_area = sum(self._calculate_box_area(p.bounding_box) for p in products)
        
        occupancy = occupied_area / shelf_area
        return min(max(occupancy, 0.0), 1.0)

    def evaluate(self, context: RetailContext) -> Optional[RetailEvent]:
        occupancy = self._get_pseudo_occupancy(context)
        
        state_key = f"{self.name}_state"
        rule_key = self.name
        
        current_state = self.state_manager.get(state_key, "NORMAL")
        
        is_empty = occupancy < self.shelf_config.empty_threshold
        is_low = not is_empty and occupancy < self.shelf_config.low_stock_threshold
        
        # State transitions
        if is_empty and current_state != "EMPTY":
            if self.debouncer.check_persistence(f"{rule_key}_empty", True, self.shelf_config.min_persistence_seconds, context.timestamp):
                if self.debouncer.check_cooldown(rule_key, self.shelf_config.cooldown_seconds, context.timestamp):
                    self.state_manager.set(state_key, "EMPTY")
                    self.debouncer.register_fire(rule_key, context.timestamp)
                    return self.event_factory.create_event(
                        event_type="SHELF_EMPTY",
                        zone_id=self.shelf_config.id,
                        severity="HIGH",
                        metadata={"occupancy": occupancy, "threshold": self.shelf_config.empty_threshold}
                    )
        elif is_low and current_state not in ["LOW", "EMPTY"]:
             if self.debouncer.check_persistence(f"{rule_key}_low", True, self.shelf_config.min_persistence_seconds, context.timestamp):
                if self.debouncer.check_cooldown(rule_key, self.shelf_config.cooldown_seconds, context.timestamp):
                    self.state_manager.set(state_key, "LOW")
                    self.debouncer.register_fire(rule_key, context.timestamp)
                    return self.event_factory.create_event(
                        event_type="SHELF_LOW_STOCK",
                        zone_id=self.shelf_config.id,
                        severity="MEDIUM",
                        metadata={"occupancy": occupancy, "threshold": self.shelf_config.low_stock_threshold}
                    )
        elif not is_empty and not is_low:
            self.state_manager.set(state_key, "NORMAL")
            
        return None
