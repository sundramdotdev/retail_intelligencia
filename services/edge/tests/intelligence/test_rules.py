import pytest
from unittest.mock import MagicMock
from app.intelligence.context import RetailContext
from app.intelligence.state import StateManager
from app.intelligence.debouncer import Debouncer
from app.events.factory import RetailEventFactory
from app.intelligence.rules.queue import QueueRule
from app.config.settings import QueueZoneConfig
from app.models.vision import TrackedObject

@pytest.fixture
def mock_factory():
    factory = MagicMock(spec=RetailEventFactory)
    factory.create_event.return_value = "MOCK_EVENT"
    return factory

def test_queue_rule_trigger_and_hysteresis(mock_factory):
    config = QueueZoneConfig(
        id="checkout",
        high_threshold=3,
        recovery_threshold=1,
        min_persistence_seconds=2.0,
        cooldown_seconds=10.0
    )
    
    sm = StateManager()
    db = Debouncer()
    rule = QueueRule(config, sm, db, mock_factory)
    
    def make_context(count, timestamp):
        tracks = []
        for i in range(count):
            tracks.append(TrackedObject(
                track_id=i, label="person", confidence=0.9,
                bounding_box=[0,0,10,10], center={"x":0,"y":0},
                first_seen=timestamp, last_seen=timestamp, age=1, current_zone="checkout"
            ))
        return RetailContext(timestamp=timestamp, device_id="test", camera_id="test", tracks=tracks, observations=[], fps_metrics={})

    # T=0: 2 people (Normal)
    assert rule.evaluate(make_context(2, 0.0)) is None
    assert sm.get("QueueRule_checkout_state", "NORMAL") == "NORMAL"
    
    # T=1: 3 people (Met threshold, but no persistence)
    assert rule.evaluate(make_context(3, 1.0)) is None
    
    # T=4: 3 people (Persistence met!)
    event = rule.evaluate(make_context(3, 4.0))
    assert event == "MOCK_EVENT"
    assert sm.get("QueueRule_checkout_state", "NORMAL") == "HIGH"
    
    # T=5: 2 people (Hysteresis prevents recovery because recovery_threshold=1)
    assert rule.evaluate(make_context(2, 5.0)) is None
    assert sm.get("QueueRule_checkout_state", "NORMAL") == "HIGH"
    
    # T=6: 1 person (Recovery threshold met)
    assert rule.evaluate(make_context(1, 6.0)) is None
    assert sm.get("QueueRule_checkout_state", "NORMAL") == "NORMAL"
