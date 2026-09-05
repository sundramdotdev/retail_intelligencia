from abc import ABC, abstractmethod
from typing import Optional
from app.intelligence.context import RetailContext
from app.events.models import RetailEvent
from app.intelligence.state import StateManager
from app.intelligence.debouncer import Debouncer
from app.events.factory import RetailEventFactory
import logging

logger = logging.getLogger("rules")

class RetailRuleResult:
    def __init__(self, triggered: bool, event_type: str = "", zone_id: str = "", severity: str = "INFO", metadata: dict = None):
        self.triggered = triggered
        self.event_type = event_type
        self.zone_id = zone_id
        self.severity = severity
        self.metadata = metadata or {}

class RetailRule(ABC):
    def __init__(self, *args, name: str = "", **kwargs):
        if len(args) == 4 and not name:
            self.name = args[0]
            self.state_manager = args[1]
            self.debouncer = args[2]
            self.event_factory = args[3]
        elif len(args) >= 3:
            self.name = name or (args[0] if len(args) == 4 else "")
            offset = 1 if len(args) == 4 else 0
            self.state_manager = args[offset]
            self.debouncer = args[offset + 1]
            self.event_factory = args[offset + 2]
        else:
            self.name = name or kwargs.get("name", "")
            self.state_manager = kwargs.get("state_manager")
            self.debouncer = kwargs.get("debouncer")
            self.event_factory = kwargs.get("event_factory")

    @abstractmethod
    def evaluate(self, context: RetailContext) -> Optional[RetailEvent]:
        """
        Evaluate the rule based on the given context.
        If the rule triggers and passes debouncing/cooldown, it must return a RetailEvent.
        Otherwise, return None.
        """
        pass
