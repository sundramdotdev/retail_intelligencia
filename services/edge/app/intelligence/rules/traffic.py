from typing import Optional
from app.intelligence.rules.base import RetailRule
from app.intelligence.context import RetailContext
from app.events.models import RetailEvent
from app.config.settings import TrafficZoneConfig

class TrafficRule(RetailRule):
    def __init__(self, zone_config: TrafficZoneConfig, *args, **kwargs):
        super().__init__(name=f"TrafficRule_{zone_config.id}", *args, **kwargs)
        self.zone_config = zone_config

    def evaluate(self, context: RetailContext) -> Optional[RetailEvent]:
        history_key = f"{self.name}_history"
        
        # Use ZONE_ENTERED observations to build traffic history
        entries = self.state_manager.get(history_key, [])
        
        for obs in context.observations:
            if obs.type == "ZONE_ENTERED" and obs.zone_id == self.zone_config.id:
                # Add (track_id, timestamp)
                entries.append((obs.track_id, obs.timestamp))
                
        # Clean up history older than window
        cutoff = context.timestamp - self.zone_config.window_seconds
        entries = [(tid, ts) for tid, ts in entries if ts >= cutoff]
        self.state_manager.set(history_key, entries)
        
        unique_entries = {tid for tid, ts in entries}
        count = len(unique_entries)
        
        state_key = f"{self.name}_state"
        rule_key = self.name
        
        current_state = self.state_manager.get(state_key, "NORMAL")
        
        if current_state == "NORMAL":
            if count >= self.zone_config.high_threshold:
                if self.debouncer.check_persistence(f"{rule_key}_high", True, self.zone_config.min_persistence_seconds, context.timestamp):
                    if self.debouncer.check_cooldown(rule_key, self.zone_config.cooldown_seconds, context.timestamp):
                        self.state_manager.set(state_key, "HIGH")
                        self.debouncer.register_fire(rule_key, context.timestamp)
                        return self.event_factory.create_event(
                            event_type="TRAFFIC_HIGH",
                            zone_id=self.zone_config.id,
                            severity="MEDIUM",
                            metadata={"entryCount": count, "windowSeconds": self.zone_config.window_seconds}
                        )
            elif count <= self.zone_config.low_threshold:
                if self.debouncer.check_persistence(f"{rule_key}_low", True, self.zone_config.min_persistence_seconds, context.timestamp):
                    if self.debouncer.check_cooldown(rule_key, self.zone_config.cooldown_seconds, context.timestamp):
                        self.state_manager.set(state_key, "LOW")
                        self.debouncer.register_fire(rule_key, context.timestamp)
                        return self.event_factory.create_event(
                            event_type="TRAFFIC_LOW",
                            zone_id=self.zone_config.id,
                            severity="LOW",
                            metadata={"entryCount": count, "windowSeconds": self.zone_config.window_seconds}
                        )
        elif current_state == "HIGH":
            if count <= self.zone_config.recovery_high_threshold:
                self.state_manager.set(state_key, "NORMAL")
        elif current_state == "LOW":
            if count >= self.zone_config.recovery_low_threshold:
                self.state_manager.set(state_key, "NORMAL")
                
        return None
