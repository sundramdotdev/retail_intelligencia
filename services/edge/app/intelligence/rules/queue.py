from typing import Optional
from app.intelligence.rules.base import RetailRule
from app.intelligence.context import RetailContext
from app.events.models import RetailEvent
from app.config.settings import QueueZoneConfig

class QueueRule(RetailRule):
    def __init__(self, zone_config: QueueZoneConfig, *args, **kwargs):
        super().__init__(name=f"QueueRule_{zone_config.id}", *args, **kwargs)
        self.zone_config = zone_config

    def evaluate(self, context: RetailContext) -> Optional[RetailEvent]:
        # Count unique people in the checkout zone
        people_in_zone = [
            t for t in context.tracks 
            if t.current_zone == self.zone_config.id and t.label == "person"
        ]
        
        # Eliminate duplicates by track_id just in case
        unique_people = {t.track_id for t in people_in_zone}
        count = len(unique_people)
        
        state_key = f"{self.name}_state"
        rule_key = self.name
        
        current_state = self.state_manager.get(state_key, "NORMAL")
        
        if current_state == "NORMAL":
            condition_met = count >= self.zone_config.high_threshold
            
            if self.debouncer.check_persistence(rule_key, condition_met, self.zone_config.min_persistence_seconds, context.timestamp):
                if self.debouncer.check_cooldown(rule_key, self.zone_config.cooldown_seconds, context.timestamp):
                    # Trigger!
                    self.state_manager.set(state_key, "HIGH")
                    self.debouncer.register_fire(rule_key, context.timestamp)
                    
                    metadata = {
                        "peopleCount": count,
                        "threshold": self.zone_config.high_threshold
                    }
                    return self.event_factory.create_event(
                        event_type="QUEUE_HIGH",
                        zone_id=self.zone_config.id,
                        severity="HIGH",
                        metadata=metadata
                    )
        
        elif current_state == "HIGH":
            # Hysteresis recovery
            if count <= self.zone_config.recovery_threshold:
                self.state_manager.set(state_key, "NORMAL")
                
        return None
