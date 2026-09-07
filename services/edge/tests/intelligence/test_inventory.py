import pytest
import time
from unittest.mock import MagicMock
from app.intelligence.rules.inventory import InventoryRule
from app.intelligence.state import StateManager
from app.intelligence.debouncer import Debouncer
from app.events.factory import RetailEventFactory
from app.config.settings import InventoryZoneConfig, Settings
from app.intelligence.context import RetailContext
from app.models.vision import TrackedObject

@pytest.fixture
def inventory_rule():
    config = InventoryZoneConfig(
        zone_id="inventory-demo",
        object_class="bottle",
        target_count=5,
        low_stock_threshold=3,
        recovery_threshold=4,
        min_persistence_seconds=0.0,
        cooldown_seconds=0.0
    )
    
    mock_settings = MagicMock()
    mock_settings.device.id = "edge-test"
    mock_settings.store.id = "store-test"
    
    rule = InventoryRule(config)
    rule.state_manager = StateManager()
    rule.debouncer = Debouncer()
    rule.event_factory = MagicMock()
    
    # Mock create_event
    def mock_create_event(*args, **kwargs):
        event = MagicMock()
        event.eventType = kwargs.get("event_type")
        event.metadata = kwargs.get("metadata")
        return event
    rule.event_factory.create_event.side_effect = mock_create_event
    
    return rule

def create_tracks(count, label="bottle", zone_id="inventory-demo"):
    tracks = []
    for i in range(count):
        t = TrackedObject(
            track_id=i,
            label=label,
            confidence=0.9,
            bounding_box=[0,0,10,10],
            center={'x': 5, 'y': 5},
            first_seen=0,
            last_seen=0,
            age=0,
            current_zone=zone_id
        )
        tracks.append(t)
    return tracks

def test_inventory_count_normal(inventory_rule):
    ctx = RetailContext(timestamp=time.time(), device_id="dev1", camera_id="cam1", tracks=create_tracks(5), observations=[], fps_metrics={})
    event = inventory_rule.evaluate(ctx)
    assert event is None
    assert inventory_rule.state_manager.get(f"{inventory_rule.name}_state", "NORMAL") == "NORMAL"

def test_inventory_threshold_low(inventory_rule):
    t = time.time()
    # 5 objects -> normal
    ctx = RetailContext(timestamp=t, device_id="dev1", camera_id="cam1", tracks=create_tracks(5), observations=[], fps_metrics={})
    inventory_rule.evaluate(ctx)
    
    # drops to 2 objects -> triggers low (first call sets persistence start, second call evaluates elapsed time)
    ctx1 = RetailContext(timestamp=t + 0.1, device_id="dev1", camera_id="cam1", tracks=create_tracks(2), observations=[], fps_metrics={})
    inventory_rule.evaluate(ctx1)
    
    ctx2 = RetailContext(timestamp=t + 0.2, device_id="dev1", camera_id="cam1", tracks=create_tracks(2), observations=[], fps_metrics={})
    event = inventory_rule.evaluate(ctx2)
    
    assert event is not None
    assert event.eventType == "INVENTORY_LOW"
    assert event.metadata["currentCount"] == 2
    assert inventory_rule.state_manager.get(f"{inventory_rule.name}_state", "NORMAL") == "LOW"

def test_inventory_recovery(inventory_rule):
    t = time.time()
    # Trigger low first
    ctx1 = RetailContext(timestamp=t, device_id="dev1", camera_id="cam1", tracks=create_tracks(2), observations=[], fps_metrics={})
    inventory_rule.evaluate(ctx1)
    ctx2 = RetailContext(timestamp=t + 0.1, device_id="dev1", camera_id="cam1", tracks=create_tracks(2), observations=[], fps_metrics={})
    inventory_rule.evaluate(ctx2)
    assert inventory_rule.state_manager.get(f"{inventory_rule.name}_state", "NORMAL") == "LOW"
    
    # Recover to 4
    ctx3 = RetailContext(timestamp=t + 0.2, device_id="dev1", camera_id="cam1", tracks=create_tracks(4), observations=[], fps_metrics={})
    inventory_rule.evaluate(ctx3)
    ctx4 = RetailContext(timestamp=t + 0.3, device_id="dev1", camera_id="cam1", tracks=create_tracks(4), observations=[], fps_metrics={})
    event = inventory_rule.evaluate(ctx4)
    
    assert event is not None
    assert event.eventType == "INVENTORY_RECOVERED"
    assert event.metadata["currentCount"] == 4
    assert inventory_rule.state_manager.get(f"{inventory_rule.name}_state", "NORMAL") == "NORMAL"

def test_inventory_debounce():
    # Setup rule with persistence delay
    config = InventoryZoneConfig(
        zone_id="inventory-demo",
        object_class="bottle",
        target_count=5,
        low_stock_threshold=3,
        recovery_threshold=4,
        min_persistence_seconds=2.0,
        cooldown_seconds=10.0
    )
    
    mock_settings = MagicMock()
    mock_settings.device.id = "edge-test"
    mock_settings.store.id = "store-test"
    
    rule = InventoryRule(config)
    rule.state_manager = StateManager()
    rule.debouncer = Debouncer()
    rule.event_factory = RetailEventFactory(mock_settings)
    
    base_time = time.time()
    
    # 5 objects -> normal
    ctx = RetailContext(timestamp=base_time, device_id="dev1", camera_id="cam1", tracks=create_tracks(5), observations=[], fps_metrics={})
    rule.evaluate(ctx)
    
    # 2 objects -> waiting for persistence
    ctx = RetailContext(timestamp=base_time + 0.5, device_id="dev1", camera_id="cam1", tracks=create_tracks(2), observations=[], fps_metrics={})
    event = rule.evaluate(ctx)
    assert event is None
    
    # 2 objects -> persistence met
    ctx = RetailContext(timestamp=base_time + 2.5, device_id="dev1", camera_id="cam1", tracks=create_tracks(2), observations=[], fps_metrics={})
    event = rule.evaluate(ctx)
    assert event is not None
    assert event.eventType == "INVENTORY_LOW"
