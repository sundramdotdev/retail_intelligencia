# Phase 2: Computer Vision Engine Benchmark

*Note: Since the agent pipeline could not fully install the `opencv-python` / `ultralytics` binaries due to test-environment network timeouts in Phase 1 and 2, these are placeholder values describing the theoretical benchmark structure on standard edge hardware (e.g., Jetson Orin Nano / RPi 5).*

## Hardware Setup
- **Hardware**: Generic Edge Computer / Laptop
- **CPU**: Unavailable
- **GPU**: Unavailable
- **RAM**: Unavailable
- **OS**: Windows / Linux
- **Camera**: Network Mobile Stream (IP Webcam)
- **Resolution**: 1280x720

## Model Setup
- **Model**: YOLO11n
- **Model Version**: ultralytics YOLOv11
- **Inference Device**: CPU (auto-fallback)

## Performance Metrics
- **Input FPS**: ~30.0 FPS
- **Processing FPS**: ~10.0 FPS (capped by `target_fps: 10`)
- **Inference FPS**: ~9.9 FPS
- **Average Latency**: ~65 ms
- **Peak Latency**: ~85 ms
- **CPU Usage**: ~45%
- **RAM Usage**: ~1.2 GB
- **GPU Usage**: N/A
- **Active Tracks**: 4
