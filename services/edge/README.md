# Retail Intelligencia - Edge Device Foundation

This directory contains the Phase 1 implementation of the edge device foundation.

## Overview
The application connects to a camera source (Network, RTSP, or USB), processes frames locally, and monitors system and camera health.

## Development Setup

1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   .\venv\Scripts\Activate.ps1  # On Windows
   pip install -r requirements.txt
   ```

2. Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   ```
   Add your `CAMERA_STREAM_URL` to `.env`.

3. Run the application:
   ```bash
   python -m app.main
   ```

## Hardware-in-the-Loop Test

1. Start mobile phone camera stream.
2. Connect phone and edge computer to same network.
3. Put stream URL into `.env` as `CAMERA_STREAM_URL`.
4. Start edge runtime (`python -m app.main`).
5. Verify Camera 01 connects.
6. Verify frames are received.
7. Verify input FPS.
8. Verify processing FPS.
9. Verify CPU/RAM metrics.
10. Move camera.
11. Verify frames continue updating.
12. Stop phone stream.
13. Verify disconnect detection.
14. Restart phone stream.
15. Verify automatic reconnection.

## Testing

```bash
python -m pytest tests/
python -m ruff check app/ tests/
```
