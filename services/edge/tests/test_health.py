import pytest
from app.monitoring.health import HealthMonitor
from app.config.settings import Settings

@pytest.fixture
def mock_config():
    return Settings(
        device={"id": "test", "name": "test"},
        camera={"id": "cam", "name": "cam", "type": "usb"},
        processing={"target_fps": 10, "resize_width": 640, "resize_height": 480},
        monitoring={
            "health_interval_seconds": 5,
            "fps_window_seconds": 5,
            "health": {
                "cpu_warning_percent": 80,
                "cpu_critical_percent": 90,
                "memory_warning_percent": 80,
                "memory_critical_percent": 90,
                "disk_warning_percent": 80,
                "disk_critical_percent": 90
            }
        },
        logging={"level": "INFO"}
    )

def test_health_monitor(mock_config):
    monitor = HealthMonitor(mock_config)
    health = monitor.get_health()
    
    assert health is not None
    assert isinstance(health.cpu_usage_percent, float)
    assert isinstance(health.memory_usage_percent, float)
    assert health.gpu_usage_percent is None  # Mocked
