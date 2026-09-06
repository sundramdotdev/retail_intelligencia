import pytest
import numpy as np
from unittest.mock import MagicMock, patch

from app.models.vision import Detection
from app.tools.object_detection_ui import ObjectDetectionApp
from app.config.settings import Settings

@pytest.fixture
def mock_config():
    # Load minimal config for testing
    config = MagicMock()
    
    config.processing = MagicMock()
    config.processing.resize_width = 1280
    config.processing.resize_height = 720
    
    config.vision = MagicMock()
    config.vision.detector = MagicMock()
    config.vision.detector.model = "models/yolo11n.pt"
    config.vision.detector.device = "cpu"
    config.vision.detector.confidence_threshold = 0.4
    
    return config

@pytest.fixture
def mock_detector():
    detector = MagicMock()
    detector.status = "READY"
    detector._class_names = {0: "person", 39: "bottle", 41: "cup"}
    detector.config = MagicMock()
    return detector

def test_object_detection_app_init(mock_config):
    with patch("app.tools.object_detection_ui.YOLODetector") as MockYOLO:
        with patch("app.main.get_camera_source"):
            with patch("app.tools.object_detection_ui.VideoStreamManager"):
                app = ObjectDetectionApp(mock_config)
                assert app.filter_mode == "ALL"
                assert app.confidence_threshold == 0.4
                assert app.canvas_width == 1280 + 450

def test_object_detection_render_all_mode(mock_config, mock_detector):
    with patch("app.tools.object_detection_ui.YOLODetector") as MockYOLO:
        with patch("app.main.get_camera_source"):
            with patch("app.tools.object_detection_ui.VideoStreamManager"):
                app = ObjectDetectionApp(mock_config)
                app.detector = mock_detector
                
                # Create a blank frame
                frame = np.zeros((720, 1280, 3), dtype=np.uint8)
                
                # Mock detections
                detections = [
                    Detection(class_id=0, label="person", confidence=0.9, bounding_box=[10, 10, 50, 50], timestamp=1.0),
                    Detection(class_id=39, label="bottle", confidence=0.8, bounding_box=[60, 60, 80, 80], timestamp=1.0)
                ]
                
                app.filter_mode = "ALL"
                canvas = app.render(frame, detections)
                
                assert canvas.shape == (720, 1730, 3)
                # Just verifying it renders without crashing

def test_object_detection_render_person_only_mode(mock_config, mock_detector):
    with patch("app.tools.object_detection_ui.YOLODetector") as MockYOLO:
        with patch("app.main.get_camera_source"):
            with patch("app.tools.object_detection_ui.VideoStreamManager"):
                app = ObjectDetectionApp(mock_config)
                app.detector = mock_detector
                
                frame = np.zeros((720, 1280, 3), dtype=np.uint8)
                detections = [
                    Detection(class_id=0, label="person", confidence=0.9, bounding_box=[10, 10, 50, 50], timestamp=1.0)
                ]
                
                app.filter_mode = "PERSON"
                canvas = app.render(frame, detections)
                
                assert canvas.shape == (720, 1730, 3)

def test_object_detection_render_empty_state(mock_config, mock_detector):
    with patch("app.tools.object_detection_ui.YOLODetector") as MockYOLO:
        with patch("app.main.get_camera_source"):
            with patch("app.tools.object_detection_ui.VideoStreamManager"):
                app = ObjectDetectionApp(mock_config)
                app.detector = mock_detector
                
                frame = np.zeros((720, 1280, 3), dtype=np.uint8)
                detections = []
                
                canvas = app.render(frame, detections)
                
                assert canvas.shape == (720, 1730, 3)
                # It should render the "NO OBJECTS DETECTED" state without crashing
