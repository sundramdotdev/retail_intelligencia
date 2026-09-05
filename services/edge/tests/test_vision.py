import pytest
import numpy as np
from unittest.mock import patch, MagicMock

from app.models.vision import Detection, TrackedObject
from app.zones.engine import ZoneEngine
from app.observations.emitter import ObservationEmitter
from app.config.settings import ZoneConfig

@pytest.fixture
def mock_zones():
    return [
        ZoneConfig(
            id="zone-a",
            name="Zone A",
            enabled=True,
            polygon=[[0, 0], [100, 0], [100, 100], [0, 100]]
        ),
        ZoneConfig(
            id="zone-b",
            name="Zone B",
            enabled=True,
            polygon=[[100, 0], [200, 0], [200, 100], [100, 100]]
        )
    ]

def test_zone_engine_membership(mock_zones):
    engine = ZoneEngine(mock_zones)
    
    # Point inside Zone A
    assert engine.get_zone_for_point(50, 50) == "zone-a"
    
    # Point inside Zone B
    assert engine.get_zone_for_point(150, 50) == "zone-b"
    
    # Point outside all zones
    assert engine.get_zone_for_point(300, 300) is None

def test_zone_engine_assignment(mock_zones):
    engine = ZoneEngine(mock_zones)
    
    obj = TrackedObject(
        track_id=1,
        label="person",
        confidence=0.9,
        bounding_box=[10, 10, 90, 90],
        center={"x": 50, "y": 50},
        first_seen=0.0,
        last_seen=0.0,
        age=1,
        current_zone=None
    )
    
    engine.assign_zones([obj])
    assert obj.current_zone == "zone-a"

def test_observation_emitter_lifecycle():
    emitter = ObservationEmitter()
    
    # 1. New object appears (enters Zone A)
    obj = TrackedObject(
        track_id=1,
        label="person",
        confidence=0.9,
        bounding_box=[],
        center={"x": 50, "y": 50},
        first_seen=0.0,
        last_seen=0.0,
        age=1,
        current_zone="zone-a"
    )
    
    obs = emitter.generate_observations([], [obj])
    assert len(obs) == 2
    types = {o.type for o in obs}
    assert "PERSON_DETECTED" in types
    assert "ZONE_ENTERED" in types
    
    # 2. Object moves to Zone B
    obj.current_zone = "zone-b"
    obs = emitter.generate_observations([], [obj])
    assert len(obs) == 1
    assert obs[0].type == "ZONE_CHANGED"
    assert obs[0].metadata["from_zone"] == "zone-a"
    assert obs[0].zone_id == "zone-b"
    
    # 3. Object leaves all zones
    obj.current_zone = None
    obs = emitter.generate_observations([], [obj])
    assert len(obs) == 1
    assert obs[0].type == "ZONE_EXITED"
    assert obs[0].zone_id == "zone-b"
    
    # 4. Object disappears
    obs = emitter.generate_observations([], [])
    assert len(obs) == 0
    assert len(emitter.previous_zones) == 0

@patch("app.detection.yolo.YOLO")
def test_yolo_detector_provisioning(mock_yolo_class):
    # This verifies that the detector will attempt to load the model and filter classes
    from app.detection.yolo import YOLODetector
    from app.config.settings import VisionConfig, DetectorConfig, ClassesConfig, TrackingConfig
    
    config = VisionConfig(
        enabled=True,
        detector=DetectorConfig(
            type="yolo",
            model="models/yolo11n.pt",
            confidence_threshold=0.5,
            iou_threshold=0.5,
            device="cpu"
        ),
        classes=ClassesConfig(enabled=["person", "bottle"]),
        tracking=TrackingConfig(enabled=True, max_lost_frames=30)
    )
    
    mock_model_instance = MagicMock()
    mock_model_instance.names = {0: "person", 1: "bicycle", 39: "bottle"}
    mock_yolo_class.return_value = mock_model_instance
    
    detector = YOLODetector(config)
    success = detector.load()
    
    assert success is True
    assert detector.status == "READY"
    mock_yolo_class.assert_called_once_with("models/yolo11n.pt")
    
    # It should only filter for person (0) and bottle (39)
    assert 0 in detector._filtered_classes
    assert 39 in detector._filtered_classes
    assert 1 not in detector._filtered_classes
