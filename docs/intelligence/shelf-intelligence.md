# Shelf Intelligence

## Purpose
Detects when a specific configured retail shelf is running low on stock or becomes completely empty.

## Input
- `TrackedObject`s intersecting the configured shelf zone.
- As YOLO11n lacks retail-specific product classes, this rule calculates pseudo-occupancy based on generic object bounding box area against the zone polygon area.

## Formula
`Occupancy = (Area of Tracked Objects) / (Area of Shelf Zone Polygon)`

## Triggers
- **SHELF_LOW_STOCK**: Occupancy drops below `low_stock_threshold` but remains above `empty_threshold`.
- **SHELF_EMPTY**: Occupancy drops below `empty_threshold`.

## Persistence & Cooldown
- Condition must persist continuously for `min_persistence_seconds`.
- Once triggered, the rule enters cooldown for `cooldown_seconds`.
- Duplicate events are suppressed entirely if the shelf remains in the same operational state (`LOW` or `EMPTY`).
