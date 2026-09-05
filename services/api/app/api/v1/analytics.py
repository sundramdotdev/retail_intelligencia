"""Analytics and operational metrics API routes."""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query, status

from app.auth.human import AuthenticatedUser, get_current_user, verify_store_access
from app.clients.data_service import data_client

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/overview", status_code=status.HTTP_200_OK)
async def get_overview(
    store_id: str = Query(..., alias="storeId"),
    user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """Store-level intelligence KPI overview."""
    verify_store_access(user, store_id)
    return await data_client.get_analytics_overview(store_id)


@router.get("/traffic", status_code=status.HTTP_200_OK)
async def get_traffic(
    store_id: str = Query(..., alias="storeId"),
    interval: str = Query("hour", pattern="^(hour|day|week)$"),
    user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """Store foot traffic counts by time interval."""
    verify_store_access(user, store_id)
    return {
        "storeId": store_id,
        "interval": interval,
        "series": [
            {"time": "09:00", "count": 22},
            {"time": "10:00", "count": 48},
            {"time": "11:00", "count": 75},
            {"time": "12:00", "count": 110},
            {"time": "13:00", "count": 92},
            {"time": "14:00", "count": 64},
        ],
    }


@router.get("/queues", status_code=status.HTTP_200_OK)
async def get_queues(
    store_id: str = Query(..., alias="storeId"),
    user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """Current checkout and queue performance metrics."""
    verify_store_access(user, store_id)
    return {
        "storeId": store_id,
        "activeRegisters": 4,
        "zones": [
            {
                "zoneId": "zone-checkout",
                "currentQueueLength": 5,
                "averageWaitSeconds": 135,
                "status": "CONGESTED",
            }
        ],
    }


@router.get("/dwell", status_code=status.HTTP_200_OK)
async def get_dwell(
    store_id: str = Query(..., alias="storeId"),
    user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """Zone dwell time aggregations."""
    verify_store_access(user, store_id)
    return {
        "storeId": store_id,
        "zones": [
            {"zoneId": "zone-aisle-01", "name": "Beverages", "averageDwellSeconds": 42},
            {"zoneId": "zone-checkout", "name": "Checkout Queue", "averageDwellSeconds": 135},
        ],
    }


@router.get("/shelves", status_code=status.HTTP_200_OK)
async def get_shelves(
    store_id: str = Query(..., alias="storeId"),
    user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """Shelf stock availability status and incident metrics."""
    verify_store_access(user, store_id)
    return {
        "storeId": store_id,
        "totalShelfZones": 6,
        "lowStockZones": 1,
        "emptyZones": 0,
        "incidentsToday": 3,
        "zones": [
            {"zoneId": "zone-aisle-01", "shelfStatus": "LOW_STOCK", "stockPercentage": 18},
        ],
    }
