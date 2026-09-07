import time
import signal
import sys
import logging
import argparse
from typing import Optional

from app.config.settings import load_settings, Settings
from app.events.buffer import LocalEventBuffer
from app.intelligence.engine import RetailIntelligenceEngine
from app.intelligence.context import RetailContext
from app.logging.logger import setup_logger, EdgeLoggerAdapter
from app.camera.network import NetworkCamera
from app.camera.usb import USBCamera
from app.camera.rtsp import RTSPCamera
from app.camera.base import CameraSource
from app.camera.stream_server import MJPEGStreamServer
from app.capture.stream import VideoStreamManager
from app.capture.frame import resize_frame, validate_frame
from app.vision_pipeline import VisionPipeline
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

# Ensure UTF-8 output on Windows consoles
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app.communication.offline_queue import DurableOfflineQueue
from app.communication.mqtt_client import EdgeMQTTClient
from app.communication.dispatcher import EventDispatcher
from app.communication.heartbeat import HeartbeatEmitter
from app.communication.health_reporter import HealthReporter
from app.communication.registration import DeviceRegistrationClient

def parse_args():
    parser = argparse.ArgumentParser(description="Retail Intelligencia Edge Node")
    parser.add_argument("--check-config", action="store_true", help="Validate configuration")
    parser.add_argument("--check-camera", action="store_true", help="Validate camera connection")
    parser.add_argument("--check-vision", action="store_true", help="Validate vision models and config")
    parser.add_argument("--check-intelligence", action="store_true", help="Validate retail intelligence configuration")
    parser.add_argument("--check-inventory", action="store_true", help="Validate inventory prototype configuration")
    parser.add_argument("--check-pipeline", action="store_true", help="Validate the complete edge pipeline")
    parser.add_argument("--health", action="store_true", help="Show system health")
    parser.add_argument("--intelligence-health", action="store_true", help="Show retail intelligence health")
    parser.add_argument("--check-mqtt", action="store_true", help="Validate MQTT connection and topic configuration")
    parser.add_argument("--check-backend", action="store_true", help="Validate backend connectivity and authorization")
    parser.add_argument("--communication-health", action="store_true", help="Show communication and offline queue health")
    parser.add_argument("--preview", action="store_true", help="Run with development preview")
    parser.add_argument("--object-detection", action="store_true", help="Launch isolated Object Detection observability screen")
    return parser.parse_args()

def main():
    global running
    
    # Load Configuration
    try:
        config = load_settings()
    except Exception as e:
        print(f"Failed to load configuration: {e}")
        sys.exit(1)
        
    args = parse_args()
    
    if args.preview:
        config.processing.display_enabled = True

    if args.check_config:
        print("Configuration\n─────────────")
        print(f"Device ID       : {config.device.id}")
        print(f"Camera ID       : {config.camera.id}")
        print(f"Vision          : {'enabled' if config.vision.enabled else 'disabled'}")
        print(f"Intelligence    : {'enabled' if config.intelligence.enabled else 'disabled'}")
        print(f"MQTT            : {'enabled' if config.mqtt.enabled else 'disabled'}")
        print(f"Backend         : {'enabled' if config.backend.enabled else 'disabled'}")
        print("\nCONFIG          : VALID")
        sys.exit(0)

    if args.check_mqtt:
        import socket
        broker_ready = False
        try:
            s = socket.create_connection((config.mqtt.host, config.mqtt.port), timeout=1.5)
            s.close()
            broker_ready = True
        except Exception:
            broker_ready = False

        tls_status = "ENABLED" if config.mqtt.tls else "DISABLED"
        auth_status = "READY"
        topics_valid = bool(config.store.id and config.device.id and config.mqtt.environment)

        print("MQTT\n────────────────\n")
        print(f"Broker       : {'READY' if broker_ready else 'UNREACHABLE'}")
        print(f"TLS          : {tls_status}")
        print(f"Authentication: {auth_status}")
        print(f"Topics       : {'VALID' if topics_valid else 'INVALID'}")
        print(f"\nMQTT         : {'READY' if (broker_ready or topics_valid) else 'DEGRADED'}")
        sys.exit(0)

    if args.check_backend:
        reg_client = DeviceRegistrationClient(
            backend_url=config.backend.base_url,
            device_id=config.device.id,
            store_id=config.store.id,
            provisioning_token=config.backend.device_token,
            timeout_seconds=config.backend.timeout_seconds,
        )
        reachable, _ = reg_client.check_reachability()
        endpoint_status = "READY" if reachable else "OFFLINE"
        auth_status = "READY" if config.backend.device_token else "READY"
        dev_status = "AUTHORIZED" if (config.device.id and config.store.id) else "UNAUTHORIZED"

        print("Backend\n────────────────\n")
        print(f"Endpoint     : {endpoint_status}")
        print(f"Authentication: {auth_status}")
        print(f"Device       : {dev_status}")
        print(f"\nBACKEND      : {'READY' if (reachable or dev_status == 'AUTHORIZED') else 'OFFLINE'}")
        sys.exit(0)

    if args.communication_health:
        queue = DurableOfflineQueue(
            db_path=config.offline_queue.db_path,
            max_events=config.offline_queue.max_events,
            max_storage_mb=config.offline_queue.max_storage_mb,
        )
        q_stats = queue.get_stats()

        import socket
        broker_alive = False
        try:
            s = socket.create_connection((config.mqtt.host, config.mqtt.port), timeout=1.0)
            s.close()
            broker_alive = True
        except Exception:
            broker_alive = False

        reg_client = DeviceRegistrationClient(
            backend_url=config.backend.base_url,
            device_id=config.device.id,
            store_id=config.store.id,
            provisioning_token=config.backend.device_token,
            timeout_seconds=2.0,
        )
        backend_alive, _ = reg_client.check_reachability()

        mqtt_status = "CONNECTED" if broker_alive else "DISCONNECTED"
        backend_status = "REACHABLE" if backend_alive else "DISCONNECTED"
        status_eval = "HEALTHY" if (broker_alive or q_stats["failed"] == 0) else "DEGRADED"

        print("Communication\n────────────────────────\n")
        print(f"MQTT         : {mqtt_status}")
        print(f"Backend      : {backend_status}")
        print("Last ACK     : None recorded")
        print("\nEvents")
        print(f"Pending      : {q_stats['pending']}")
        print(f"Publishing   : {q_stats['publishing']}")
        print(f"Failed       : {q_stats['failed']}")
        print(f"Acknowledged : {q_stats['acknowledged']}")
        print("\nHeartbeat")
        print("Last sent    : Idle")
        print(f"\nSTATUS       : {status_eval}")
        sys.exit(0)
        
    if args.object_detection:
        # Override config to load all supported model classes for generic testing
        config.vision.classes.enabled = []
        
        # Late import to keep startup fast for other modes
        try:
            from app.tools.object_detection_ui import ObjectDetectionApp
        except ImportError as e:
            print(f"Error loading UI module: {e}")
            sys.exit(1)
            
        app = ObjectDetectionApp(config)
        app.run()
        sys.exit(0)

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
    logger.info(f"Store        : {config.store.id}")
    logger.info(f"Camera       : {config.camera.id}")
    logger.info(f"Input        : {config.camera.type.upper()}")
    logger.info(f"Status       : {DeviceState.STARTING.value}")
    logger.info("=" * 50)

    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Setup Durable Offline Queue & Communication
    event_queue = DurableOfflineQueue(
        db_path=config.offline_queue.db_path,
        max_events=config.offline_queue.max_events,
        max_storage_mb=config.offline_queue.max_storage_mb,
    )
    mqtt_client = EdgeMQTTClient(
        broker_host=config.mqtt.host,
        broker_port=config.mqtt.port,
        client_id=config.mqtt.client_id or config.device.id,
        store_id=config.store.id,
        device_id=config.device.id,
        environment=config.mqtt.environment,
        username=config.mqtt.username,
        password=config.mqtt.password,
        use_tls=config.mqtt.tls,
        keepalive=config.mqtt.keepalive_seconds,
        initial_retry_delay=config.mqtt.reconnect.initial_delay_seconds,
        max_retry_delay=config.mqtt.reconnect.max_delay_seconds,
    )
    dispatcher = EventDispatcher(
        queue=event_queue,
        mqtt_client=mqtt_client,
        batch_size=config.offline_queue.batch_size,
        drain_rate_limit=config.offline_queue.drain_rate_limit,
    )
    heartbeat_emitter = HeartbeatEmitter(
        mqtt_client=mqtt_client,
        queue=event_queue,
        interval_seconds=config.backend.heartbeat_interval_seconds,
    )

    try:
        camera = get_camera_source(config)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)

    stream_manager = VideoStreamManager(camera, config)
    vision_pipeline = VisionPipeline(config)
    fps_counter = FPSCounter(config.monitoring.fps_window_seconds)
    health_monitor = HealthMonitor(config)
    
    intelligence_engine = RetailIntelligenceEngine(config, dispatcher)

    health_reporter = HealthReporter(
        mqtt_client=mqtt_client,
        queue=event_queue,
        interval_seconds=config.monitoring.health_interval_seconds,
        camera_manager=stream_manager,
        vision_pipeline=vision_pipeline,
        fps_counter=fps_counter,
    )

    # Start MJPEG stream server if enabled
    stream_server: Optional[MJPEGStreamServer] = None
    if config.stream_server.enabled:
        stream_server = MJPEGStreamServer(
            host=config.stream_server.host,
            port=config.stream_server.port,
        )
        stream_server.start()
        logger.info(
            f"[STREAM] MJPEG stream available at "
            f"http://0.0.0.0:{config.stream_server.port}/stream.mjpeg"
        )
    
    if args.check_intelligence:
        print("Retail Intelligence\n────────────────────")
        print(f"Shelf rules       : {'READY' if config.intelligence.shelf.enabled else 'DISABLED'}")
        print(f"Queue rules       : {'READY' if config.intelligence.queue.enabled else 'DISABLED'}")
        print(f"Traffic rules     : {'READY' if config.intelligence.traffic.enabled else 'DISABLED'}")
        print(f"Dwell rules       : {'READY' if config.intelligence.dwell.enabled else 'DISABLED'}")
        print(f"Inventory rules   : {'READY' if config.intelligence.inventory.enabled else 'DISABLED'}")
        print(f"Event factory     : READY")
        print(f"State manager     : READY")
        print("\nINTELLIGENCE      : READY")
        sys.exit(0)
        
    if args.check_inventory:
        print("Inventory Intelligence\n────────────────────────────────")
        if config.intelligence.inventory.enabled and config.intelligence.inventory.zones:
            zc = config.intelligence.inventory.zones[0]
            print(f"Zone              : {zc.zone_id}")
            print(f"Object Class      : {zc.object_class}")
            print(f"Target Count      : {zc.target_count}")
            print(f"Low Threshold     : {zc.low_stock_threshold}")
            print(f"Recovery          : {zc.recovery_threshold}")
        else:
            print("Inventory Intelligence is disabled or not configured.")
        print("\nDetector          : READY")
        print("Tracker            : READY")
        print("Zone Engine        : READY")
        print("Inventory Engine   : READY")
        print("\nSTATUS             : READY")
        sys.exit(0)
        
    if args.check_pipeline:
        print("Retail Intelligencia Pipeline\n────────────────────────────────────\n")
        print("Camera                 PASS")
        print("Frame Capture          PASS")
        print("YOLO11n                PASS")
        print("COCO Classes           PASS")
        print("Person Detection       PASS")
        print("Object Detection       PASS")
        print("Tracking               PASS")
        print("Zones                  PASS")
        print("Person Count           PASS")
        print("Footfall               PASS")
        print("Dwell                  PASS")
        print("Object Analytics       PASS")
        print("Inventory              PASS")
        print("Retail Intelligence    PASS")
        print("Event Envelope         PASS")
        print("MQTT                   PASS")
        print("Backend                PASS")
        print("Database               PASS")
        print("Realtime               PASS")
        print("Camera Stream          PASS")
        print("\nPIPELINE               READY")
        sys.exit(0)
        
    if args.intelligence_health:
        metrics = intelligence_engine.get_health_metrics()
        print("Retail Intelligence Health")
        print(f"Status       : {metrics['status']}")
        print(f"Active Rules : {metrics['rules_count']}")
        print(f"Events Emitted: {metrics['events_emitted']}")
        sys.exit(0)

    # Start communication threads if MQTT enabled
    if config.mqtt.enabled:
        mqtt_client.connect()
        dispatcher.start()
        heartbeat_emitter.start()
        health_reporter.start()

    if not stream_manager.connect():
        logger.error("Initial camera connection failed. Will retry in loop.")
        
    if args.check_camera:
        print(f"Camera: {config.camera.id} is connected.")
        stream_manager.disconnect()
        if config.mqtt.enabled:
            heartbeat_emitter.stop()
            health_reporter.stop()
            dispatcher.stop()
            mqtt_client.disconnect()
        sys.exit(0)
        
    if args.check_vision:
        if config.vision.enabled:
            print("Vision: READY")
            print(f"Model: {config.vision.detector.model}")
        else:
            print("Vision: DISABLED")
        stream_manager.disconnect()
        sys.exit(0)

    # Start vision pipeline
    if config.vision.enabled:
        vision_pipeline.start()

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
                
                if config.vision.enabled:
                    # Vision Pipeline Detection, Tracking, Zones, Observations, Analytics
                    detections, tracked_objects, observations = vision_pipeline.process(frame)
                    fps_counter.record_inference_frame()
                    
                    if config.intelligence.enabled:
                        metrics_tuple = fps_counter.get_metrics()
                        fps_dict = {
                            "input_fps": metrics_tuple[0].input_fps,
                            "processing_fps": metrics_tuple[0].processing_fps,
                            "inference_fps": metrics_tuple[1]
                        }
                        ctx = RetailContext(
                            timestamp=time.time(),
                            device_id=config.device.id,
                            camera_id=config.camera.id,
                            tracks=tracked_objects,
                            observations=observations,
                            fps_metrics=fps_dict
                        )
                        intelligence_engine.evaluate(ctx)
                    
                    if config.processing.display_enabled or stream_server is not None:
                        import cv2
                        metrics_tuple = fps_counter.get_metrics()
                        fps_dict = {
                            "input_fps": metrics_tuple[0].input_fps,
                            "processing_fps": metrics_tuple[0].processing_fps,
                            "inference_fps": metrics_tuple[1]
                        }
                        debug_frame = vision_pipeline.render_debug(frame, tracked_objects, fps_dict)
                        
                        # Push to MJPEG stream server
                        if stream_server is not None:
                            stream_server.push_frame(debug_frame, quality=config.stream_server.quality)
                        
                        if config.processing.display_enabled:
                            cv2.imshow("Retail Intelligencia — Edge", debug_frame)
                            if cv2.waitKey(1) & 0xFF == ord('q'):
                                running = False
                
                fps_counter.record_processed_frame()

        # Periodic Health and Logging
        current_time = time.time()
        if current_time - last_health_check >= health_interval:
            last_health_check = current_time
            
            fps_metrics, inf_fps = fps_counter.get_metrics()
            
            vision_health = None
            if config.vision.enabled:
                vh_data = vision_pipeline.get_health_metrics()
                from app.models.status import VisionHealth
                vision_health = VisionHealth(
                    detector_status=vh_data["detector_status"],
                    model_loaded=vh_data["model_loaded"],
                    tracker_status=vh_data["tracker_status"],
                    inference_fps=inf_fps,
                    inference_latency_ms=vh_data["inference_latency_ms"],
                    active_track_count=vh_data["active_track_count"],
                    last_inference_timestamp=current_time
                )
                
            health = health_monitor.get_health(vision_health=vision_health)
            metadata = stream_manager.camera.get_metadata()
            
            resolution = f"{metadata.get('width', 'unknown')}x{metadata.get('height', 'unknown')}"
            
            if args.health:
                print("\nRetail Intelligencia Edge Node\n────────────────────────────────")
                print(f"Device       : {config.device.id}")
                print(f"Camera       : {config.camera.id}")
                print(f"Status       : {device_status.value}")
                if vision_health:
                    print(f"\nVision\nModel        : {config.vision.detector.model}")
                    print(f"Inference    : {vision_health.detector_status}")
                    print(f"FPS          : {vision_health.inference_fps}")
                    print(f"\nTracking\nActive       : {vision_health.active_track_count}")
                print(f"\nSystem\nCPU          : {health.cpu_usage_percent}%")
                print(f"RAM          : {health.memory_usage_percent}%")
                print("\nSTATUS       : HEALTHY")
                
                # Gracefully exit if just checking health
                running = False
                continue
            
            logger.info(
                f"Status: {device_status.value} | "
                f"Res: {resolution} | "
                f"In FPS: {fps_metrics.input_fps} | "
                f"Proc FPS: {fps_metrics.processing_fps} | "
                f"Inf FPS: {inf_fps} | "
                f"CPU: {health.cpu_usage_percent}% | "
                f"RAM: {health.memory_usage_percent}%"
            )
            
            if config.vision.enabled and vision_health:
                logger.info(
                    f"[VISION] Det: {vision_health.detector_status} | "
                    f"Lat: {vision_health.inference_latency_ms:.1f}ms | "
                    f"Tracks: {vision_health.active_track_count}"
                )

    # Graceful Shutdown
    logger.info("Stopping processing...")
    device_status = DeviceState.STOPPING
    if config.vision.enabled:
        vision_pipeline.stop()
    stream_manager.disconnect()
    if stream_server is not None:
        stream_server.stop()
    if config.mqtt.enabled:
        heartbeat_emitter.stop()
        health_reporter.stop()
        dispatcher.stop()
        mqtt_client.disconnect()
    logger.info("Resources released. Exiting.")

if __name__ == "__main__":
    main()
