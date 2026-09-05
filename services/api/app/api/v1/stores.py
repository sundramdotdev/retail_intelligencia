"""Store and zone management API routes."""
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.human import AuthenticatedUser, get_current_user, verify_store_access
from app.clients.data_service import data_client

router = APIRouter(prefix="/stores", tags=["Stores"])


@router.get("", status_code=status.HTTP_200_OK)
async def get_stores(
    user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """List stores accessible to the authenticated user."""
    stores = await data_client.get_stores()
    if user.role != "PLATFORM_ADMIN":
        stores = [s for s in stores if s.get("storeId") == user.store_id]
    return {"count": len(stores), "stores": stores}


@router.get("/{store_id}", status_code=status.HTTP_200_OK)
async def get_store_by_id(
    store_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """Retrieve detailed store configuration."""
    verify_store_access(user, store_id)
    store = await data_client.get_store_by_id(store_id)
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "STORE_NOT_FOUND", "message": f"Store '{store_id}' not found."}},
        )
    return store


@router.get("/{store_id}/zones", status_code=status.HTTP_200_OK)
async def get_store_zones(
    store_id: str,
    user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """Retrieve all physical detection zones (aisles, shelves, queues) configured for this store."""
    verify_store_access(user, store_id)
    zones = await data_client.get_store_zones(store_id)
    return {"storeId": store_id, "count": len(zones), "zones": zones}
