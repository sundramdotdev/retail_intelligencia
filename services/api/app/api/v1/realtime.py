"""SSE (Server-Sent Events) streaming endpoint for realtime dashboard updates.

Provides store-scoped event streams to authenticated dashboard clients.
Channels: ALERT_TRIGGERED, TASK_UPDATED, EVENT_RECEIVED, DEVICE_STATUS, ZONE_TELEMETRY
"""
import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse

from app.auth.human import AuthenticatedUser, get_current_user, verify_store_access
from app.realtime.broadcaster import broadcaster

router = APIRouter(prefix="/realtime", tags=["Realtime"])
logger = logging.getLogger("api.realtime")

HEARTBEAT_INTERVAL = 15  # seconds


async def sse_event_generator(
    request: Request,
    store_id: str,
    user: AuthenticatedUser,
):
    """Generate SSE events for a connected dashboard client."""
    conn = await broadcaster.subscribe(
        store_id=store_id,
        user_id=user.user_id,
        role=user.role,
    )

    try:
        # Send initial connection confirmation
        yield f"event: connected\ndata: {{\"storeId\": \"{store_id}\", \"userId\": \"{user.user_id}\", \"role\": \"{user.role}\"}}\n\n"

        while True:
            # Check if client disconnected
            if await request.is_disconnected():
                break

            try:
                # Wait for event with timeout for heartbeat
                message = await asyncio.wait_for(
                    conn.queue.get(),
                    timeout=HEARTBEAT_INTERVAL,
                )
                yield f"event: message\ndata: {message}\n\n"
            except asyncio.TimeoutError:
                # Send heartbeat ping to keep connection alive
                yield f"event: heartbeat\ndata: {{\"type\": \"ping\"}}\n\n"

    except asyncio.CancelledError:
        pass
    finally:
        await broadcaster.unsubscribe(conn)


@router.get("/stream", response_class=StreamingResponse)
async def realtime_stream(
    request: Request,
    store_id: str = Query(..., alias="storeId"),
    user: AuthenticatedUser = Depends(get_current_user),
):
    """SSE stream delivering store-scoped realtime events to dashboard clients.

    Channels:
    - ALERT_TRIGGERED: New operational alert created
    - TASK_UPDATED: Task status change (assigned, in progress, completed)
    - EVENT_RECEIVED: New retail event ingested
    - DEVICE_STATUS: Device heartbeat or status change
    - ZONE_TELEMETRY: Zone occupancy update

    Connection states (client-side):
    - LIVE: Receiving events normally
    - RECONNECTING: Connection lost, attempting reconnect
    - OFFLINE: Unable to reconnect
    """
    verify_store_access(user, store_id)

    return StreamingResponse(
        sse_event_generator(request, store_id, user),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.get("/status")
async def realtime_status(
    user: AuthenticatedUser = Depends(get_current_user),
):
    """Get current realtime connection statistics."""
    return {
        "totalConnections": broadcaster.total_connections,
        "status": "OPERATIONAL",
    }
