import time
import signal
import sys
import logging
from typing import Optional

from app.config.settings import load_settings, Settings
from app.logging.logger import setup_logger, EdgeLoggerAdapter
from app.camera.network import NetworkCamera
from app.camera.usb import USBCamera
from app.camera.rtsp import RTSPCamera
from app.camera.base import CameraSource
from app.capture.stream import VideoStreamManager
from app.capture.frame import resize_frame, validate_frame
from app.detection.basic import BasicDetector
from app.monitoring.fps import FPSCounter
from app.monitoring.health import HealthMonitor
from app.models.status import DeviceState

# Global state for graceful shutdown
running = True

def signal_handler(sig, frame):
    global running
    print('\nInitiating graceful shutdown...')
    running = False

def get_camera_source(config: Settings) -> CameraSource:
    cam_type = config.camera.type.lower()
    if cam_type == "network":
        if not config.camera.url:
            raise ValueError("CAMERA_STREAM_URL must be provided for network camera.")
        return NetworkCamera(config.camera.id, config.camera.url)
    elif cam_type == "usb":
        return USBCamera(config.camera.id, config.camera.device_index)
    elif cam_type == "rtsp":
        if not config.camera.url:
            raise ValueError("CAMERA_STREAM_URL must be provided for rtsp camera.")
        return RTSPCamera(config.camera.id, config.camera.url)
    else:
        raise ValueError(f"Unsupported camera type: {cam_type}")

def main():
    global running
    
    # Load Configuration
    try:
        config = load_settings()
    except Exception as e:
        print(f"Failed to load configuration: {e}")
        sys.exit(1)

    # Setup Logging
    base_logger = setup_logger("edge", config.logging.level)
    logger = EdgeLoggerAdapter(base_logger, {'device_id': config.device.id})
    camera_logger = EdgeLoggerAdapter(logging.getLogger("camera"), {'device_id': config.device.id})
    stream_logger = EdgeLoggerAdapter(logging.getLogger("stream"), {'device_id': config.device.id})
    monitoring_logger = EdgeLoggerAdapter(logging.getLogger("monitoring"), {'device_id': config.device.id})
    
    logger.info("=" * 50)
    logger.info("RETAIL INTELLIGENCIA — EDGE NODE")
    logger.info("=" * 50)
    logger.info(f"Device       : {config.device.id}")
    logger.info(f"Camera       : {config.camera.id}")
    logger.info(f"Input        : {config.camera.type.upper()}")
    logger.info(f"Status       : {DeviceState.STARTING.value}")
    logger.info("=" * 50)

    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        camera = get_camera_source(config)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)

    stream_manager = VideoStreamManager(camera, config)
    detector = BasicDetector()
    fps_counter = FPSCounter(config.monitoring.fps_window_seconds)
    health_monitor = HealthMonitor(config)

    # Initial Connection
    if not stream_manager.connect():
        logger.error("Initial camera connection failed. Will retry in loop.")

    # Main Loop State
    last_health_check = time.time()
    health_interval = config.monitoring.health_interval_seconds
    device_status = DeviceState.READY

    while running:
        if not stream_manager.camera.is_connected():
            stream_manager.handle_reconnect()
            continue
            
        success, frame, should_process = stream_manager.read_and_sample()
        
        if not success:
            logger.warning("Failed to read from camera. Attempting reconnect...")
            stream_manager.disconnect()
            continue

        fps_counter.record_input_frame()
        device_status = DeviceState.STREAMING

        if should_process:
            if validate_frame(frame):
                # Optional Resize
                frame = resize_frame(frame, config.processing.resize_width, config.processing.resize_height)
                
                # Basic Detection
                result = detector.detect(frame)
                
                fps_counter.record_processed_frame()

        # Periodic Health and Logging
        current_time = time.time()
        if current_time - last_health_check >= health_interval:
            last_health_check = current_time
            
            fps = fps_counter.get_metrics()
            health = health_monitor.get_health()
            metadata = stream_manager.camera.get_metadata()
            
            resolution = f"{metadata.get('width', 'unknown')}x{metadata.get('height', 'unknown')}"
            
            logger.info(
                f"Status: {device_status.value} | "
                f"Res: {resolution} | "
                f"In FPS: {fps.input_fps} | "
                f"Proc FPS: {fps.processing_fps} | "
                f"CPU: {health.cpu_usage_percent}% | "
                f"RAM: {health.memory_usage_percent}%"
            )

    # Graceful Shutdown
    logger.info("Stopping processing...")
    device_status = DeviceState.STOPPING
    stream_manager.disconnect()
    logger.info("Resources released. Exiting.")

if __name__ == "__main__":
    main()
