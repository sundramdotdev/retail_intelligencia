# Traffic Intelligence

## Purpose
Measures footfall entering a specific zone over a rolling time window, alerting on significant surges or lulls in customer traffic.

## Input
- Stream of `ZONE_ENTERED` observations mapped to unique `track_id`s.

## Formula
Counts unique `track_id` entries that occurred within the last `window_seconds`.

## Triggers
- **TRAFFIC_HIGH**: Entry count `>= high_threshold`
- **TRAFFIC_LOW**: Entry count `<= low_threshold`

## State transitions
- Transition to `HIGH` requires exceeding `high_threshold`.
- Return to `NORMAL` from `HIGH` requires dropping to `recovery_high_threshold`.
- Transition to `LOW` requires dropping to `low_threshold`.
- Return to `NORMAL` from `LOW` requires exceeding `recovery_low_threshold`.

## Persistence & Cooldown
- High/Low conditions must persist for `min_persistence_seconds` before an event is generated.
- After an event, the rule respects `cooldown_seconds`.
