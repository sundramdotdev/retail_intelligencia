# Analytics API & Store Metrics

The Analytics API (`/api/v1/analytics/*`) provides real-time operational insights derived from the edge event stream for store managers and corporate dashboards.

---

## 1. Endpoints Specification

### A. Store KPI Overview
`GET /api/v1/analytics/overview?storeId=store_001`

Returns top-level operational health indicators:
```json
{
  "storeId": "store_001",
  "activeQueues": 1,
  "averageWaitSeconds": 120,
  "footTrafficCurrentHour": 45,
  "lowStockIncidentsToday": 2,
  "deviceHealthStatus": "ONLINE"
}
```

### B. Foot Traffic Breakdown
`GET /api/v1/analytics/traffic?storeId=store_001&interval=hour`

Returns hourly or daily entrance and aisle traversal counts:
```json
{
  "storeId": "store_001",
  "interval": "hour",
  "series": [
    {"time": "09:00", "count": 22},
    {"time": "10:00", "count": 48},
    {"time": "11:00", "count": 75},
    {"time": "12:00", "count": 110},
    {"time": "13:00", "count": 92},
    {"time": "14:00", "count": 64}
  ]
}
```

### C. Queue & Checkout Performance
`GET /api/v1/analytics/queues?storeId=store_001`

Provides real-time line lengths and queue congestion statuses:
```json
{
  "storeId": "store_001",
  "activeRegisters": 4,
  "zones": [
    {
      "zoneId": "zone-checkout",
      "currentQueueLength": 5,
      "averageWaitSeconds": 135,
      "status": "CONGESTED"
    }
  ]
}
```

### D. Zone Dwell Time
`GET /api/v1/analytics/dwell?storeId=store_001`

Summarizes customer dwell times across promotional displays and aisles:
```json
{
  "storeId": "store_001",
  "zones": [
    {"zoneId": "zone-aisle-01", "name": "Beverages", "averageDwellSeconds": 42},
    {"zoneId": "zone-checkout", "name": "Checkout Queue", "averageDwellSeconds": 135}
  ]
}
```

### E. Shelf Availability & Stockout Incidents
`GET /api/v1/analytics/shelves?storeId=store_001`

Monitors shelf stock percentages and cumulative stockout alerts:
```json
{
  "storeId": "store_001",
  "totalShelfZones": 6,
  "lowStockZones": 1,
  "emptyZones": 0,
  "incidentsToday": 3,
  "zones": [
    {"zoneId": "zone-aisle-01", "shelfStatus": "LOW_STOCK", "stockPercentage": 18}
  ]
}
```
