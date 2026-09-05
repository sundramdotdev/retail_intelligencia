from collections import deque
from typing import List
import logging
from app.events.models import RetailEvent

logger = logging.getLogger("events")

class LocalEventBuffer:
    def __init__(self, max_size: int = 100):
        self.buffer = deque(maxlen=max_size)

    def add(self, event: RetailEvent):
        self.buffer.append(event)
        
        # Pretty print to console for development/demo
        print(f"\n[{event.timestamp}] {event.eventType}")
        print(f"Zone      : {event.zoneId}")
        print(f"Severity  : {event.severity}")
        for k, v in event.metadata.items():
            print(f"{k.capitalize():<10}: {v}")
        print("-" * 30)
        
        logger.info(f"Generated retail event: {event.eventType} in {event.zoneId}")

    def get_recent(self) -> List[RetailEvent]:
        return list(self.buffer)
