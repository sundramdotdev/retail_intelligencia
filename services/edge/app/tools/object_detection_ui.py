import cv2
import numpy as np
import time
import logging
from typing import List, Dict, Any

from app.config.settings import Settings
from app.detection.yolo import YOLODetector
from app.capture.stream import VideoStreamManager
from app.capture.frame import resize_frame, validate_frame
from app.models.vision import Detection

logger = logging.getLogger("object_detection_ui")

class ObjectDetectionApp:
    def __init__(self, config: Settings):
        self.config = config
        self.detector = YOLODetector(config.vision)
        # Bypassing the network camera logic if needed, but it's better to use the same initialization as main.py
        from app.main import get_camera_source
        self.camera = get_camera_source(config)
        self.stream_manager = VideoStreamManager(self.camera, config)
        
        self.window_name = "Retail Intelligencia - Object Detection Observer"
        
        # Display settings
        self.sidebar_width = 450
        self.frame_width = config.processing.resize_width or 1280
        self.frame_height = config.processing.resize_height or 720
        self.canvas_width = self.frame_width + self.sidebar_width
        self.canvas_height = self.frame_height
        
        # UI State
        self.filter_mode = "ALL"  # ALL, PERSON, NON_PERSON
        self.confidence_threshold = self.config.vision.detector.confidence_threshold
        
        # Diagnostics
        self.last_inference_latency = 0.0
        self.input_fps = 0.0
        self.inference_fps = 0.0
        self.last_input_time = time.time()
        self.last_inference_time = time.time()
        self.frame_count = 0
        self.inf_count = 0
        
        # Rolling logs
        self.detection_logs = []
        
        # Colors
        self.colors = {
            "bg": (20, 20, 20),
            "text": (230, 230, 230),
            "text_dim": (150, 150, 150),
            "accent": (255, 153, 51),  # BGR for a premium blue/orange
            "person_box": (0, 255, 0),
            "other_box": (255, 100, 100),
            "error": (0, 0, 255),
            "ok": (0, 255, 0)
        }

    def _draw_text(self, canvas, text, x, y, scale=0.5, color=None, thickness=1, font=cv2.FONT_HERSHEY_SIMPLEX):
        if color is None:
            color = self.colors["text"]
        cv2.putText(canvas, text, (int(x), int(y)), font, scale, color, thickness, cv2.LINE_AA)

    def run(self):
        print(f"Starting isolated Object Detection UI...")
        self.detector.load()
        if not self.stream_manager.connect():
            print("Failed to connect to camera. Will retry in loop.")

        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, self.canvas_width, self.canvas_height)

        running = True
        while running:
            # Reconnect logic
            if not self.stream_manager.camera.is_connected():
                self.stream_manager.handle_reconnect()
                # Create a placeholder canvas
                canvas = np.full((self.canvas_height, self.canvas_width, 3), self.colors["bg"], dtype=np.uint8)
                self._draw_text(canvas, "CAMERA DISCONNECTED - Waiting for reconnection...", 50, self.canvas_height // 2, scale=1.0, color=self.colors["error"], thickness=2)
                cv2.imshow(self.window_name, canvas)
                if cv2.waitKey(100) & 0xFF == 27:  # ESC
                    break
                continue

            # Read frame
            success, frame, should_process = self.stream_manager.read_and_sample()
            if not success or not validate_frame(frame):
                continue
                
            # FPS tracking
            now = time.time()
            self.frame_count += 1
            if now - self.last_input_time >= 1.0:
                self.input_fps = self.frame_count / (now - self.last_input_time)
                self.frame_count = 0
                self.last_input_time = now

            # Process frame
            display_frame = resize_frame(frame, self.frame_width, self.frame_height)
            detections = []
            
            # Apply dynamic threshold to config so YOLO uses it
            self.detector.config.confidence_threshold = self.confidence_threshold
            
            if should_process and self.detector.status == "READY":
                t0 = time.time()
                raw_detections = self.detector.detect(display_frame)
                t1 = time.time()
                
                self.last_inference_latency = (t1 - t0) * 1000
                self.inf_count += 1
                if now - self.last_inference_time >= 1.0:
                    self.inference_fps = self.inf_count / (now - self.last_inference_time)
                    self.inf_count = 0
                    self.last_inference_time = now

                # Filter detections based on UI mode
                for d in raw_detections:
                    is_person = (d.label.lower() == "person")
                    if self.filter_mode == "PERSON" and not is_person:
                        continue
                    if self.filter_mode == "NON_PERSON" and is_person:
                        continue
                    detections.append(d)
                    
                # Update logs
                if len(detections) > 0:
                    ts_str = time.strftime("%H:%M:%S", time.localtime(t1))
                    top_d = sorted(detections, key=lambda x: x.confidence, reverse=True)[0]
                    self.detection_logs.append(f"[{ts_str}] {top_d.label} {top_d.confidence:.2f}")
                    if len(self.detection_logs) > 8:
                        self.detection_logs.pop(0)

            # Render UI
            canvas = self.render(display_frame, detections)
            cv2.imshow(self.window_name, canvas)

            # Key controls
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                running = False
            elif key == ord('c') or key == ord('C'):
                modes = ["ALL", "PERSON", "NON_PERSON"]
                self.filter_mode = modes[(modes.index(self.filter_mode) + 1) % len(modes)]
            elif key == ord('='): # + key
                self.confidence_threshold = min(0.99, self.confidence_threshold + 0.05)
            elif key == ord('-'): # - key
                self.confidence_threshold = max(0.01, self.confidence_threshold - 0.05)

        self.stream_manager.disconnect()
        self.detector.unload()
        cv2.destroyAllWindows()

    def render(self, frame: np.ndarray, detections: List[Detection]) -> np.ndarray:
        # Create full canvas
        canvas = np.full((self.canvas_height, self.canvas_width, 3), self.colors["bg"], dtype=np.uint8)
        
        # 1. Draw detections on frame
        frame_copy = frame.copy()
        persons_count = 0
        others_count = 0
        
        for d in detections:
            x1, y1, x2, y2 = map(int, d.bounding_box)
            is_person = (d.label.lower() == "person")
            if is_person:
                persons_count += 1
            else:
                others_count += 1
                
            color = self.colors["person_box"] if is_person else self.colors["other_box"]
            cv2.rectangle(frame_copy, (x1, y1), (x2, y2), color, 2)
            
            # Label background
            label_text = f"{d.label} {d.confidence:.2f}"
            (tw, th), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(frame_copy, (x1, y1 - th - 5), (x1 + tw, y1), color, -1)
            self._draw_text(frame_copy, label_text, x1, y1 - 2, color=(0, 0, 0))

        if len(detections) == 0 and self.detector.status == "READY":
            self._draw_text(frame_copy, "NO OBJECTS DETECTED", self.frame_width // 2 - 150, self.frame_height // 2, scale=1.0, color=self.colors["accent"], thickness=2)
            self._draw_text(frame_copy, f"Threshold: {self.confidence_threshold:.2f}", self.frame_width // 2 - 80, self.frame_height // 2 + 30, color=self.colors["text_dim"])

        # Place frame on canvas
        canvas[0:self.frame_height, 0:self.frame_width] = frame_copy

        # 2. Draw Sidebar
        sx = self.frame_width + 20
        sy = 30
        
        # Header
        self._draw_text(canvas, "OBJECT DETECTION OBSERVER", sx, sy, scale=0.7, color=self.colors["accent"], thickness=2)
        sy += 30
        cv2.line(canvas, (sx, sy), (self.canvas_width - 20, sy), self.colors["text_dim"], 1)
        sy += 20
        
        # Model Info
        model_name = self.config.vision.detector.model.split('/')[-1]
        self._draw_text(canvas, f"Model  : {model_name}", sx, sy)
        sy += 20
        self._draw_text(canvas, f"Device : {self.config.vision.detector.device.upper()}", sx, sy)
        sy += 20
        
        status_color = self.colors["ok"] if self.detector.status == "READY" else self.colors["error"]
        self._draw_text(canvas, f"Status : {self.detector.status}", sx, sy, color=status_color)
        sy += 30
        
        # Performance
        self._draw_text(canvas, "PERFORMANCE", sx, sy, color=self.colors["accent"])
        sy += 20
        self._draw_text(canvas, f"Input FPS     : {self.input_fps:.1f}", sx, sy)
        sy += 20
        self._draw_text(canvas, f"Inference FPS : {self.inference_fps:.1f}", sx, sy)
        sy += 20
        self._draw_text(canvas, f"Latency       : {self.last_inference_latency:.1f} ms", sx, sy)
        sy += 30

        # Controls & Filter
        self._draw_text(canvas, "CONTROLS", sx, sy, color=self.colors["accent"])
        sy += 20
        self._draw_text(canvas, f"Confidence : {self.confidence_threshold:.2f}  [Press +/- to adjust]", sx, sy)
        sy += 20
        self._draw_text(canvas, f"Filter Mode: {self.filter_mode}  [Press C to change]", sx, sy)
        sy += 30

        # Diagnostics
        self._draw_text(canvas, "DIAGNOSTICS", sx, sy, color=self.colors["accent"])
        sy += 20
        self._draw_text(canvas, f"Objects in Frame  : {len(detections)}", sx, sy)
        sy += 20
        self._draw_text(canvas, f"Persons           : {persons_count}", sx, sy)
        sy += 20
        self._draw_text(canvas, f"Non-person Objects: {others_count}", sx, sy)
        sy += 30
        
        # Retail Insight Hint
        if others_count == 0 and persons_count > 0 and self.filter_mode != "PERSON":
            self._draw_text(canvas, "NOTE: Person detected, but no objects.", sx, sy, color=self.colors["text_dim"])
            sy += 20
            self._draw_text(canvas, "If retail product is visible, model may", sx, sy, color=self.colors["text_dim"], scale=0.4)
            sy += 15
            self._draw_text(canvas, "not be trained for it (generic YOLO).", sx, sy, color=self.colors["text_dim"], scale=0.4)
            sy += 25
            
        # Model Classes
        self._draw_text(canvas, "SUPPORTED MODEL CLASSES", sx, sy, color=self.colors["accent"])
        sy += 20
        
        if self.detector.status == "READY":
            # Just grab the first ~15-20 classes to show what it detects
            all_classes = list(self.detector._class_names.values())
            sample_classes = all_classes[:15]
            if len(all_classes) > 15:
                sample_classes.append(f"...and {len(all_classes)-15} more")
                
            class_str_1 = ", ".join(sample_classes[:8])
            class_str_2 = ", ".join(sample_classes[8:])
            
            self._draw_text(canvas, class_str_1, sx, sy, scale=0.4, color=self.colors["text_dim"])
            sy += 15
            self._draw_text(canvas, class_str_2, sx, sy, scale=0.4, color=self.colors["text_dim"])
        else:
            self._draw_text(canvas, "Loading...", sx, sy, scale=0.4, color=self.colors["text_dim"])
        sy += 30
        
        # Detection Log
        self._draw_text(canvas, "RECENT DETECTIONS", sx, sy, color=self.colors["accent"])
        sy += 20
        for log in self.detection_logs:
            self._draw_text(canvas, log, sx, sy, scale=0.45)
            sy += 15

        return canvas
