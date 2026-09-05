import os
import pytest
from app.config.settings import load_settings, Settings
import yaml
import tempfile

def test_load_settings_success():
    # Create a temporary valid config file
    config_data = {
        "device": {"id": "test-dev", "name": "Test Device"},
        "camera": {"id": "cam-1", "name": "Cam 1", "type": "network", "url": "http://test", "device_index": 0},
        "processing": {"target_fps": 10, "resize_width": 640, "resize_height": 480, "display_enabled": False},
        "monitoring": {
            "health_interval_seconds": 1,
            "fps_window_seconds": 2,
            "health": {
                "cpu_warning_percent": 80,
                "cpu_critical_percent": 90,
                "memory_warning_percent": 80,
                "memory_critical_percent": 90,
                "disk_warning_percent": 80,
                "disk_critical_percent": 90
            }
        },
        "logging": {"level": "DEBUG"}
    }
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        temp_name = f.name
        
    try:
        settings = load_settings(temp_name)
        assert isinstance(settings, Settings)
        assert settings.device.id == "test-dev"
        assert settings.processing.target_fps == 10
    finally:
        os.remove(temp_name)

def test_load_settings_env_override():
    config_data = {
        "device": {"id": "test-dev", "name": "Test Device"},
        "camera": {"id": "cam-1", "name": "Cam 1", "type": "network", "url": "http://test", "device_index": 0},
        "processing": {"target_fps": 10, "resize_width": 640, "resize_height": 480, "display_enabled": False},
        "monitoring": {
            "health_interval_seconds": 1,
            "fps_window_seconds": 2,
            "health": {
                "cpu_warning_percent": 80, "cpu_critical_percent": 90,
                "memory_warning_percent": 80, "memory_critical_percent": 90,
                "disk_warning_percent": 80, "disk_critical_percent": 90
            }
        },
        "logging": {"level": "DEBUG"}
    }
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config_data, f)
        temp_name = f.name
        
    os.environ["EDGE_DEVICE_ID"] = "override-dev"
    os.environ["CAMERA_STREAM_URL"] = "http://override"
    
    try:
        settings = load_settings(temp_name)
        assert settings.device.id == "override-dev"
        assert settings.camera.url == "http://override"
    finally:
        os.environ.pop("EDGE_DEVICE_ID")
        os.environ.pop("CAMERA_STREAM_URL")
        os.remove(temp_name)

def test_load_settings_missing_file():
    with pytest.raises(FileNotFoundError):
        load_settings("nonexistent_file.yaml")
