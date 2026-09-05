"""Event ingestion and retrieval API routes."""
import logging
from typing import Any, Dict, List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth.device import AuthenticatedDevice, get_authenticated_device
from app.auth.human import AuthenticatedUser, get_current_user, verify_store_access
from app.clients.data_service import data_client
from app.models.retail_event import CanonicalRetailEvent, EventBatchPayload
from app.realtime.broadcaster import broadcaster

router = APIRouter(prefix="/events", tags=["Events"])
logger = logging.getLogger("api.events")


@router.post("", status_code=status.HTTP_200_OK)
async def ingest_events(
    payload: Union[CanonicalRetailEvent, EventBatchPayload, List[CanonicalRetailEvent]],
    device: AuthenticatedDevice = Depends(get_authenticated_device),
) -> Dict[str, Any]:
    """Ingest one or more canonical retail events from an authenticated edge device."""
    # Normalize payload into a list of CanonicalRetailEvent
    events: List[CanonicalRetailEvent] = []
    if isinstance(payload, CanonicalRetailEvent):
        events = [payload]
    elif isinstance(payload, EventBatchPayload):
        events = payload.events
    elif isinstance(payload, list):
        events = payload

    if not events:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"code": "EMPTY_BATCH", "message": "Batch contains no events."}},
        )

    # Validate device and store boundary match
    for evt in events:
        if evt.storeId != device.store_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "STORE_MISMATCH",
                        "message": f"Device registered to '{device.store_id}' cannot publish events for '{evt.storeId}'.",
                    }
                },
            )
        if evt.deviceId != device.device_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": {
                        "code": "DEVICE_MISMATCH",
                        "message": f"Device credential '{device.device_id}' does not match event deviceId '{evt.deviceId}'.",
                    }
                },
            )

    serialized = [evt.model_dump() for evt in events]
    result = await data_client.ingest_events(serialized)

    # Broadcast accepted events to SSE dashboard clients
    accepted_count = result.get("acceptedCount", 0)
    if accepted_count > 0:
        for evt_data in serialized:
            await broadcaster.broadcast(
                store_id=evt_data.get("storeId", device.store_id),
                event_type="EVENT_RECEIVED",
                data=evt_data,
            )

    return {
        "status": "SUCCESS",
        "accepted": accepted_count,
        "duplicates": result.get("duplicateCount", 0),
        "total": result.get("totalProcessed", len(events)),
    }


@router.get("", status_code=status.HTTP_200_OK)
async def get_events(
    store_id: str = Query(..., alias="storeId"),
    zone_id: Optional[str] = Query(None, alias="zoneId"),
    limit: int = Query(50, ge=1, le=500),
    user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """Retrieve historical retail events for a store."""
    verify_store_access(user, store_id)
    items = await data_client.get_events(store_id=store_id, limit=limit, zone_id=zone_id)
    return {
        "storeId": store_id,
        "count": len(items),
        "items": items,
    }


@router.get("/{event_id}", status_code=status.HTTP_200_OK)
async def get_event_by_id(
    event_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """Retrieve a single retail event by ID."""
    event = await data_client.get_event_by_id(event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "EVENT_NOT_FOUND", "message": f"Event '{event_id}' not found."}},
        )

    verify_store_access(user, event.get("storeId", ""))
    return event
