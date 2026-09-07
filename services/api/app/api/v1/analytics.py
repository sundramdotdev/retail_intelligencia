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
    return await data_client.get_traffic(store_id, interval)


@router.get("/queues", status_code=status.HTTP_200_OK)
async def get_queues(
    store_id: str = Query(..., alias="storeId"),
    user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """Current checkout and queue performance metrics."""
    verify_store_access(user, store_id)
    return await data_client.get_queues(store_id)


@router.get("/dwell", status_code=status.HTTP_200_OK)
async def get_dwell(
    store_id: str = Query(..., alias="storeId"),
    user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """Zone dwell time aggregations."""
    verify_store_access(user, store_id)
    return await data_client.get_dwell(store_id)


@router.get("/shelves", status_code=status.HTTP_200_OK)
async def get_shelves(
    store_id: str = Query(..., alias="storeId"),
    user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """Shelf stock availability status and incident metrics."""
    verify_store_access(user, store_id)
    return await data_client.get_shelves(store_id)
