import time
from collections import deque
from app.models.status import FPSMetrics

class FPSCounter:
    def __init__(self, window_seconds: int = 5):
        self.window_seconds = window_seconds
        self.input_frames = deque()
        self.processed_frames = deque()
        self.inference_frames = deque()

    def record_input_frame(self):
        self.input_frames.append(time.time())

    def record_processed_frame(self):
        self.processed_frames.append(time.time())
        
    def record_inference_frame(self):
        self.inference_frames.append(time.time())

    def _cleanup_old_frames(self, frames: deque, current_time: float):
        while frames and (current_time - frames[0]) > self.window_seconds:
            frames.popleft()

    def get_metrics(self) -> tuple:
        current_time = time.time()
        
        self._cleanup_old_frames(self.input_frames, current_time)
        self._cleanup_old_frames(self.processed_frames, current_time)
        self._cleanup_old_frames(self.inference_frames, current_time)
        
        # Avoid division by zero
        if self.window_seconds <= 0:
            return FPSMetrics(input_fps=0.0, processing_fps=0.0), 0.0

        # Actual window might be smaller than window_seconds if just started
        # but to be smooth we can divide by the elapsed time up to window_seconds
        # A simpler robust way: just divide count by window_seconds for a rolling average
        # if enough time has passed, else divide by elapsed time
        
        input_fps = len(self.input_frames) / self.window_seconds
        processing_fps = len(self.processed_frames) / self.window_seconds
        inference_fps = len(self.inference_frames) / self.window_seconds

        return FPSMetrics(
            input_fps=round(input_fps, 1),
            processing_fps=round(processing_fps, 1)
        ), round(inference_fps, 1)
