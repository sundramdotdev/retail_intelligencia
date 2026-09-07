import time
import logging
from typing import List

from app.config.settings import Settings
from app.events.models import RetailEvent
from app.events.factory import RetailEventFactory
from app.events.buffer import LocalEventBuffer

from app.intelligence.context import RetailContext
from app.intelligence.state import StateManager
from app.intelligence.debouncer import Debouncer
from app.intelligence.rules.shelf import ShelfRule
from app.intelligence.rules.queue import QueueRule
from app.intelligence.rules.traffic import TrafficRule
from app.intelligence.rules.dwell import DwellRule
from app.intelligence.rules.inventory import InventoryRule

logger = logging.getLogger("intelligence")

class RetailIntelligenceEngine:
    def __init__(self, config: Settings, event_buffer: LocalEventBuffer):
        self.config = config
        self.event_buffer = event_buffer
        self.state_manager = StateManager()
        self.debouncer = Debouncer()
        self.event_factory = RetailEventFactory(config)
        self.rules = []
        
        self.last_evaluation = 0.0
        self.interval = config.intelligence.evaluation.interval_seconds
        
        self._initialize_rules()

    def _initialize_rules(self):
        if not self.config.intelligence.enabled:
            return
            
        conf = self.config.intelligence
        all_zones = self.config.zones
        
        if conf.shelf.enabled:
            for zc in conf.shelf.zones:
                self.rules.append(ShelfRule(zc, all_zones, self.state_manager, self.debouncer, self.event_factory))
                
        if conf.queue.enabled:
            for zc in conf.queue.zones:
                self.rules.append(QueueRule(zc, self.state_manager, self.debouncer, self.event_factory))
                
        if conf.traffic.enabled:
            for zc in conf.traffic.zones:
                self.rules.append(TrafficRule(zc, self.state_manager, self.debouncer, self.event_factory))
                
        if conf.dwell.enabled:
            for zc in conf.dwell.zones:
                self.rules.append(DwellRule(zc, self.state_manager, self.debouncer, self.event_factory))
                
        if conf.inventory.enabled:
            for zc in conf.inventory.zones:
                self.rules.append(InventoryRule(zc, self.state_manager, self.debouncer, self.event_factory))
                
        logger.info(f"Initialized {len(self.rules)} retail rules.")

    def evaluate(self, context: RetailContext):
        if not self.config.intelligence.enabled:
            return

        current_time = time.time()
        
        # Rate limiting logic
        if current_time - self.last_evaluation < self.interval:
            return
            
        # Stale context protection
        if current_time - context.timestamp > self.config.intelligence.evaluation.max_data_age_seconds:
            logger.warning("Skipping intelligence evaluation due to stale context.")
            return

        self.last_evaluation = current_time

        for rule in self.rules:
            try:
                event = rule.evaluate(context)
                if event:
                    self.event_buffer.add(event)
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.name}: {e}")

    def get_health_metrics(self) -> dict:
        return {
            "status": "READY",
            "rules_count": len(self.rules),
            "events_emitted": len(self.event_buffer.buffer)
        }
