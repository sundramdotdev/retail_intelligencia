"""Metrics API endpoints for realtime and historical operational data."""
from typing import Any, Dict
from fastapi import APIRouter, Depends, Query, status

from app.auth.human import AuthenticatedUser, get_current_user, verify_store_access
from app.realtime.metrics_store import live_metrics_store
from app.clients.data_service import data_client

router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.get("/live", status_code=status.HTTP_200_OK)
async def get_live_metrics(
    store_id: str = Query(..., alias="storeId"),
    user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get the latest live metrics snapshot for a store from the in-memory cache.
    Updated continuously by the MQTT consumer.
    """
    verify_store_access(user, store_id)
    metrics = live_metrics_store.get_for_store(store_id)
    
    if not metrics:
        return {
            "storeId": store_id,
            "status": "NO_DATA",
            "message": "No live metrics received from edge devices.",
        }
    
    return metrics


@router.get("/historical", status_code=status.HTTP_200_OK)
async def get_historical_metrics(
    store_id: str = Query(..., alias="storeId"),
    metric_type: str = Query(..., alias="metricType"),
    limit: int = Query(100, le=1000),
    user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Get historical metrics (from PostgreSQL via Data Service).
    """
    verify_store_access(user, store_id)
    # Forward to Data Service
    return await data_client.get_historical_metrics(store_id, metric_type, limit)
