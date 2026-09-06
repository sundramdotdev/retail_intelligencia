# Object Detection Observability

The Edge node includes a dedicated Object Detection observability interface. This tool visualizes the raw perception layer (YOLO) *before* any tracking, spatial mapping, or retail intelligence logic is applied.

## Purpose

The observability screen serves three critical diagnostic purposes:
1. **Prove Generic Model Readiness:** Verify that YOLO is functioning, hardware inference is running, and bounding boxes are accurately placed on generic objects (e.g., persons, laptops, bottles, cups).
2. **Clarify AI Capabilities vs. Reality:** Demonstrate the actual classes that the currently loaded model supports. A pretrained YOLO11n model does *not* inherently know what "Shampoo" or a "Chips packet" is.
3. **Isolate Failures:** If a retail intelligence rule is not firing (e.g., Shelf Low Stock), this tool answers: *Is the detector completely failing to see the product, or is the spatial logic ignoring it?*

## Launching the Screen

To run the isolated Object Detection screen, use the Edge Node CLI:

```powershell
cd c:\hackathon\retail_intelligencia\services\edge
python -m app.main --object-detection
```

## Features

- **Live Camera View:** Renders bounding boxes and confidences for raw detections.
- **Dynamic Threshold Adjustment:** Press `+` or `-` to dynamically adjust the confidence threshold without modifying `edge.yaml`.
- **Class Filtering:** Press `C` to cycle between filtering modes: `ALL`, `PERSON`, and `NON_PERSON`.
- **Model Truth:** Displays the exact model loaded (e.g., `yolo11n.pt`) and the actual first 15-20 classes supported by its internal class map.
- **Bypass Efficiency:** Bypasses `Norfair` tracking, `ZoneEngine`, and `MQTT` to dedicate maximum CPU to inference visualization.

## Important Note on Retail Products

The default `yolo11n.pt` model is trained on the standard COCO dataset. It supports generic classes like `person`, `bottle`, `cup`, `chair`, and `laptop`.

**It does NOT support specific retail SKUs.**

If you place a packet of supermarket biscuits in front of the camera and the screen does not draw a bounding box around it, **the pipeline is not broken.** The generic model simply does not recognize that product class. 

True retail product detection (e.g., detecting "Brand X Cola" or "Store Brand Cereal") requires replacing `yolo11n.pt` with a custom-trained retail YOLO model in future deployment phases. The architecture is already prepared to accept this swap seamlessly.
