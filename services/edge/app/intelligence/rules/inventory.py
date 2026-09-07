from typing import Optional
from app.intelligence.rules.base import RetailRule
from app.intelligence.context import RetailContext
from app.events.models import RetailEvent
from app.config.settings import InventoryZoneConfig

class InventoryRule(RetailRule):
    def __init__(self, zone_config: InventoryZoneConfig, *args, **kwargs):
        super().__init__(name=f"InventoryRule_{zone_config.zone_id}", *args, **kwargs)
        self.zone_config = zone_config

    def evaluate(self, context: RetailContext) -> Optional[RetailEvent]:
        # Count unique objects of the target class in the inventory zone
        objects_in_zone = [
            t for t in context.tracks 
            if t.current_zone == self.zone_config.zone_id and t.label == self.zone_config.object_class
        ]
        
        unique_objects = {t.track_id for t in objects_in_zone}
        count = len(unique_objects)
        
        state_key = f"{self.name}_state"
        rule_key = self.name
        
        current_state = self.state_manager.get(state_key, "NORMAL")
        
        if current_state == "NORMAL":
            condition_met = count <= self.zone_config.low_stock_threshold
            
            if self.debouncer.check_persistence(rule_key, condition_met, self.zone_config.min_persistence_seconds, context.timestamp):
                if self.debouncer.check_cooldown(rule_key, self.zone_config.cooldown_seconds, context.timestamp):
                    # Trigger!
                    self.state_manager.set(state_key, "LOW")
                    self.debouncer.register_fire(rule_key, context.timestamp)
                    
                    metadata = {
                        "objectClass": self.zone_config.object_class,
                        "currentCount": count,
                        "threshold": self.zone_config.low_stock_threshold,
                        "targetCount": self.zone_config.target_count
                    }
                    return self.event_factory.create_event(
                        event_type="INVENTORY_LOW",
                        zone_id=self.zone_config.zone_id,
                        severity="HIGH",
                        metadata=metadata
                    )
        
        elif current_state == "LOW":
            # Hysteresis recovery
            condition_met = count >= self.zone_config.recovery_threshold
            
            if self.debouncer.check_persistence(f"{rule_key}_recovery", condition_met, self.zone_config.min_persistence_seconds, context.timestamp):
                self.state_manager.set(state_key, "NORMAL")
                
                metadata = {
                    "objectClass": self.zone_config.object_class,
                    "currentCount": count,
                    "threshold": self.zone_config.low_stock_threshold,
                    "targetCount": self.zone_config.target_count
                }
                return self.event_factory.create_event(
                    event_type="INVENTORY_RECOVERED",
                    zone_id=self.zone_config.zone_id,
                    severity="INFO",
                    metadata=metadata
                )
                
        return None
