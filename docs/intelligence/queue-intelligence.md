# Queue Intelligence

## Purpose
Detects when customer queues exceed operational capacity, triggering an event to alert staff or open another checkout lane.

## Input
- Unique active `TrackedObject`s located inside the configured checkout zone.

## Formula
`queue_count = count(unique(TrackedObjects in zone))`

## Triggers
- **QUEUE_HIGH**: `queue_count >= high_threshold`

## Hysteresis & State
Queue intelligence implements hysteresis to prevent oscillation:
- To enter `HIGH` state, count must exceed `high_threshold`.
- Once `HIGH`, the queue does not return to `NORMAL` state until the count drops below `recovery_threshold`.

## Persistence & Cooldown
- Condition must persist continuously for `min_persistence_seconds`.
- Once triggered, the rule enters cooldown for `cooldown_seconds`.
- Duplicate `QUEUE_HIGH` events are suppressed while the state remains `HIGH`.
