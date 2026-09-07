"""
MJPEG HTTP Stream Server for Retail Intelligencia Edge Node.

Serves a browser-compatible MJPEG stream of the processed camera feed
with YOLO detection overlays drawn by the vision pipeline.

Architecture:
  Camera → OpenCV → YOLO → render_debug() → JPEG → MJPEG HTTP stream → Browser

This is Option B (Frame Transport) from the camera streaming architecture:
  - Does NOT expose raw RTSP credentials to the browser
  - Browser receives processed JPEG frames with detection overlays
  - No raw video escapes the edge device — only annotated JPEG snapshots

Endpoint: GET http://{edge_host}:{port}/stream.mjpeg
          GET http://{edge_host}:{port}/frame.jpg  (single frame snapshot)
          GET http://{edge_host}:{port}/health      (JSON health check)
"""
import io
import json
import logging
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger("camera.stream_server")

# ─── Shared Frame Buffer ──────────────────────────────────────────────────────

class FrameBuffer:
    """Thread-safe single-slot frame buffer for the latest processed frame."""

    def __init__(self):
        self._frame: Optional[bytes] = None  # JPEG bytes
        self._lock = threading.Lock()
        self._frame_count: int = 0
        self._last_update: float = 0.0

    def push(self, frame_bgr: np.ndarray, quality: int = 80) -> None:
        """Encode a BGR frame to JPEG and store it."""
        try:
            _, encoded = cv2.imencode(".jpg", frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, quality])
            jpeg_bytes = encoded.tobytes()
            with self._lock:
                self._frame = jpeg_bytes
                self._frame_count += 1
                self._last_update = time.time()
        except Exception as e:
            logger.debug(f"Frame encode error: {e}")

    def get(self) -> Optional[bytes]:
        """Get the latest JPEG frame bytes, or None if not available."""
        with self._lock:
            return self._frame

    @property
    def frame_count(self) -> int:
        with self._lock:
            return self._frame_count

    @property
    def last_update(self) -> float:
        with self._lock:
            return self._last_update

    @property
    def age_seconds(self) -> float:
        with self._lock:
            return time.time() - self._last_update if self._last_update > 0 else 999.0


# Global frame buffer — shared between the vision pipeline and the stream server
frame_buffer = FrameBuffer()


# ─── HTTP Request Handler ─────────────────────────────────────────────────────

class MJPEGHandler(BaseHTTPRequestHandler):
    """HTTP handler serving MJPEG stream and single-frame snapshots."""

    BOUNDARY = b"frame"
    STALE_TIMEOUT = 5.0  # seconds before declaring feed stale

    def log_message(self, format, *args):
        # Suppress default HTTP access logs (too noisy in prod)
        pass

    def do_GET(self):
        if self.path == "/stream.mjpeg":
            self._serve_mjpeg()
        elif self.path in ("/frame.jpg", "/snapshot"):
            self._serve_snapshot()
        elif self.path == "/health":
            self._serve_health()
        else:
            self.send_error(404)

    def _serve_mjpeg(self):
        """Stream MJPEG: multipart/x-mixed-replace with JPEG frames."""
        self.send_response(200)
        self.send_header("Content-Type", f"multipart/x-mixed-replace; boundary={self.BOUNDARY.decode()}")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        logger.info(f"MJPEG client connected from {self.client_address[0]}")

        try:
            while True:
                jpeg = frame_buffer.get()

                if jpeg is None or frame_buffer.age_seconds > self.STALE_TIMEOUT:
                    # Send a placeholder "waiting" frame
                    jpeg = self._make_waiting_frame()

                # Write MJPEG boundary + frame
                self.wfile.write(
                    b"--" + self.BOUNDARY + b"\r\n"
                    b"Content-Type: image/jpeg\r\n"
                    b"Content-Length: " + str(len(jpeg)).encode() + b"\r\n\r\n"
                    + jpeg + b"\r\n"
                )
                self.wfile.flush()
                time.sleep(0.05)  # ~20 fps max send rate

        except (BrokenPipeError, ConnectionResetError):
            logger.debug(f"MJPEG client disconnected from {self.client_address[0]}")
        except Exception as e:
            logger.debug(f"MJPEG stream error: {e}")

    def _serve_snapshot(self):
        """Serve a single JPEG frame."""
        jpeg = frame_buffer.get()
        if jpeg is None:
            jpeg = self._make_waiting_frame()

        self.send_response(200)
        self.send_header("Content-Type", "image/jpeg")
        self.send_header("Content-Length", str(len(jpeg)))
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(jpeg)

    def _serve_health(self):
        """Serve JSON health info about the stream server."""
        age = frame_buffer.age_seconds
        status = "STREAMING" if age < self.STALE_TIMEOUT else "STALE"
        payload = json.dumps({
            "status": status,
            "frameCount": frame_buffer.frame_count,
            "frameAgeSec": round(age, 2),
            "streamUrl": "/stream.mjpeg",
        }).encode()

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)

    @staticmethod
    def _make_waiting_frame() -> bytes:
        """Generate a placeholder JPEG frame when no camera data is available."""
        img = np.zeros((360, 640, 3), dtype=np.uint8)
        img[:] = (20, 20, 20)  # Dark gray
        cv2.putText(img, "CAMERA OFFLINE", (160, 160), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (80, 80, 80), 2)
        cv2.putText(img, "Waiting for edge device...", (130, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (60, 60, 60), 1)
        _, encoded = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 70])
        return encoded.tobytes()


# ─── Server Lifecycle ─────────────────────────────────────────────────────────

class MJPEGStreamServer:
    """Manages the MJPEG HTTP server lifecycle in a daemon thread."""

    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self._server: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False

    def start(self) -> None:
        if self._running:
            return
        try:
            self._server = HTTPServer((self.host, self.port), MJPEGHandler)
            self._thread = threading.Thread(
                target=self._server.serve_forever,
                name="MJPEGStreamServer",
                daemon=True,
            )
            self._thread.start()
            self._running = True
            logger.info(f"MJPEG stream server started at http://{self.host}:{self.port}/stream.mjpeg")
        except OSError as e:
            logger.error(f"Failed to start MJPEG stream server on port {self.port}: {e}")

    def stop(self) -> None:
        if self._server:
            self._server.shutdown()
            self._running = False
            logger.info("MJPEG stream server stopped.")

    def push_frame(self, frame_bgr: np.ndarray, quality: int = 75) -> None:
        """Push a new processed BGR frame to the stream buffer."""
        frame_buffer.push(frame_bgr, quality)

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def stream_url(self) -> str:
        return f"http://0.0.0.0:{self.port}/stream.mjpeg"
