from typing import Optional
from app.intelligence.rules.base import RetailRule
from app.intelligence.context import RetailContext
from app.events.models import RetailEvent
from app.config.settings import DwellZoneConfig

class DwellRule(RetailRule):
    def __init__(self, zone_config: DwellZoneConfig, *args, **kwargs):
        super().__init__(name=f"DwellRule_{zone_config.id}", *args, **kwargs)
        self.zone_config = zone_config

    def evaluate(self, context: RetailContext) -> Optional[RetailEvent]:
        timers_key = f"{self.name}_timers"
        emitted_key = f"{self.name}_emitted"
        
        active_tracks = {t.track_id for t in context.tracks}
        
        # Process new entries and exits from observations
        for obs in context.observations:
            if obs.track_id is None: continue
            
            if obs.type == "ZONE_ENTERED" and obs.zone_id == self.zone_config.id:
                self.state_manager.update_dict(timers_key, str(obs.track_id), context.timestamp)
                
            elif obs.type == "ZONE_CHANGED":
                if obs.metadata.get("from_zone") == self.zone_config.id:
                    self.state_manager.remove_dict(timers_key, str(obs.track_id))
                    self.state_manager.remove_dict(emitted_key, str(obs.track_id))
                elif obs.zone_id == self.zone_config.id:
                    self.state_manager.update_dict(timers_key, str(obs.track_id), context.timestamp)
                    
            elif obs.type == "ZONE_EXITED" and obs.zone_id == self.zone_config.id:
                self.state_manager.remove_dict(timers_key, str(obs.track_id))
                self.state_manager.remove_dict(emitted_key, str(obs.track_id))

        timers = self.state_manager.get(timers_key, {})
        emitted = self.state_manager.get(emitted_key, {})
        
        # Clean up lost tracks
        to_delete = []
        for tid_str in timers.keys():
            if int(tid_str) not in active_tracks:
                to_delete.append(tid_str)
        
        for tid_str in to_delete:
            self.state_manager.remove_dict(timers_key, tid_str)
            self.state_manager.remove_dict(emitted_key, tid_str)

        # Check durations
        for tid_str, entry_time in list(timers.items()):
            if tid_str in emitted:
                continue # Already emitted dwell time for this track in this session
                
            duration = context.timestamp - entry_time
            if duration >= self.zone_config.min_duration_seconds:
                rule_key = f"{self.name}_{tid_str}"
                if self.debouncer.check_cooldown(rule_key, self.zone_config.cooldown_seconds, context.timestamp):
                    self.debouncer.register_fire(rule_key, context.timestamp)
                    self.state_manager.update_dict(emitted_key, tid_str, True)
                    
                    return self.event_factory.create_event(
                        event_type="ZONE_DWELL",
                        zone_id=self.zone_config.id,
                        severity="LOW",
                        metadata={"trackId": int(tid_str), "durationSeconds": round(duration, 1)}
                    )
        return None
