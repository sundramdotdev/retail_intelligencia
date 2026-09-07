import os
import pytest
import numpy as np
from unittest.mock import MagicMock, patch

from app.camera.network import NetworkCamera
from app.models.status import CameraState
from app.config.settings import load_settings

def test_settings_env_camera_stream_url_override(tmp_path):
    config_file = tmp_path / "edge.yaml"
    config_file.write_text("""
device:
  id: edge-dev-test
  name: Test Edge Node
camera:
  id: camera-01
  name: Camera 01
  type: usb
  device_index: 0
processing:
  target_fps: 10
  resize_width: 640
  resize_height: 480
monitoring:
  health_interval_seconds: 5
  fps_window_seconds: 5
  health:
    cpu_warning_percent: 80.0
    cpu_critical_percent: 95.0
    memory_warning_percent: 80.0
    memory_critical_percent: 95.0
    disk_warning_percent: 80.0
    disk_critical_percent: 90.0
logging:
  level: INFO
""")

    with patch.dict(os.environ, {"CAMERA_STREAM_URL": "http://10.34.11.4:8080/video"}):
        settings = load_settings(str(config_file))
        assert settings.camera.url == "http://10.34.11.4:8080/video"
        assert settings.camera.type == "network"

@patch("cv2.VideoCapture")
def test_network_camera_connect_success(mock_videocapture):
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    mock_videocapture.return_value = mock_cap

    cam = NetworkCamera("cam-net-01", "http://10.34.11.4:8080/video")
    assert cam.state == CameraState.DISCONNECTED

    success = cam.connect()
    assert success is True
    assert cam.state == CameraState.CONNECTED
    assert cam.is_connected() is True
    mock_cap.set.assert_called_once()

@patch("cv2.VideoCapture")
def test_network_camera_read(mock_videocapture):
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = True
    fake_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    mock_cap.read.return_value = (True, fake_frame)
    mock_cap.get.side_effect = lambda prop: 1280 if prop == 3 else (720 if prop == 4 else 30.0)
    mock_videocapture.return_value = mock_cap

    cam = NetworkCamera("cam-net-01", "http://10.34.11.4:8080/video")
    cam.connect()

    ret, frame = cam.read()
    assert ret is True
    assert frame is not None
    assert frame.shape == (720, 1280, 3)
    assert cam.state == CameraState.STREAMING

    meta = cam.get_metadata()
    assert meta["width"] == 1280
    assert meta["height"] == 720
    assert meta["fps"] == 30.0

@patch("cv2.VideoCapture")
def test_network_camera_connect_failure(mock_videocapture):
    mock_cap = MagicMock()
    mock_cap.isOpened.return_value = False
    mock_videocapture.return_value = mock_cap

    cam = NetworkCamera("cam-net-01", "http://invalid-stream-url/video")
    success = cam.connect()
    assert success is False
    assert cam.state == CameraState.ERROR
    assert cam.is_connected() is False
