# Mobile Camera Development

During Phase 1, development is done using a mobile phone camera to simulate a physical edge camera.

## Architecture

```text
Phone Camera
     ↓
Phone Streaming/Webcam App
     ↓
Wi-Fi
     ↓
Local IP/Stream URL
     ↓
Edge Computer
     ↓
OpenCV
```

## Setup Instructions

1. Install a mobile webcam application (e.g., IP Webcam for Android, EpocCam for iOS, or DroidCam).
2. Connect both your mobile phone and your Edge Computer to the same local Wi-Fi network.
3. Start the video stream on the mobile app. Note the local IP and port provided by the app (e.g., `http://192.168.1.100:8080/video`).
4. In your `.env` file, set the URL:
   ```env
   CAMERA_STREAM_URL=http://192.168.1.100:8080/video
   ```

## Independence

Any mobile-camera solution that exposes a compatible local video stream (HTTP, MJPEG, RTSP) can be used during development. The edge runtime is completely agnostic to the specific phone application used.
