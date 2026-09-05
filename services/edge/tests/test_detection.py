import numpy as np
from app.detection.basic import BasicDetector
from app.models.status import DetectionResult

def test_basic_detection_valid_frame():
    detector = BasicDetector()
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    
    result = detector.detect(frame)
    
    assert isinstance(result, DetectionResult)
    assert result.label == "pipeline_test"
    assert result.confidence == 1.0
    assert result.bounding_box == [10.0, 10.0, 80.0, 80.0]

def test_basic_detection_empty_frame():
    detector = BasicDetector()
    result = detector.detect(None)
    assert result is None
