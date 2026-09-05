import time
from app.monitoring.fps import FPSCounter

def test_fps_calculation():
    # Patch time to mock time flow
    counter = FPSCounter(window_seconds=1)
    
    # Simulate 10 frames in 1 second
    for _ in range(10):
        counter.record_input_frame()
        
    metrics_res = counter.get_metrics()
    metrics = metrics_res[0] if isinstance(metrics_res, tuple) else metrics_res
    assert metrics.input_fps == 10.0
    assert metrics.processing_fps == 0.0

def test_fps_rolling_window(monkeypatch):
    counter = FPSCounter(window_seconds=1)
    
    current_time = 100.0
    monkeypatch.setattr(time, "time", lambda: current_time)
    
    # 5 frames at t=100
    for _ in range(5):
        counter.record_input_frame()
        
    metrics_res = counter.get_metrics()
    metrics = metrics_res[0] if isinstance(metrics_res, tuple) else metrics_res
    assert metrics.input_fps == 5.0
    
    # Move time forward by 2 seconds (past window)
    current_time = 102.0
    metrics_res = counter.get_metrics()
    metrics = metrics_res[0] if isinstance(metrics_res, tuple) else metrics_res
    assert metrics.input_fps == 0.0
