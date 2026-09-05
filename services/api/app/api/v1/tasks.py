"""Staff task dispatch and resolution routes."""
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth.human import AuthenticatedUser, get_current_user, verify_store_access
from app.clients.data_service import data_client

router = APIRouter(prefix="/tasks", tags=["Tasks"])


class CreateTaskPayload(BaseModel):
    storeId: str
    zoneId: Optional[str] = None
    type: str = Field(..., json_schema_extra={"example": "RESTOCK_SHELF"})
    priority: str = Field(default="MEDIUM", json_schema_extra={"example": "HIGH"})
    title: str = Field(..., json_schema_extra={"example": "Restock Aisle 1 Soda Cans"})
    description: Optional[str] = Field(None)
    assignedUserId: Optional[str] = None


class AssignTaskPayload(BaseModel):
    assignedUserId: str = Field(...)


class CompleteTaskPayload(BaseModel):
    resolutionNotes: str = Field(default="Task completed.", json_schema_extra={"example": "Restocked 24 units from backroom."})


@router.get("", status_code=status.HTTP_200_OK)
async def get_tasks(
    store_id: str = Query(..., alias="storeId"),
    status_filter: Optional[str] = Query(None, alias="status"),
    user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """List staff actionable tasks for a store."""
    verify_store_access(user, store_id)
    tasks = await data_client.get_tasks(store_id=store_id, status=status_filter)
    return {"storeId": store_id, "count": len(tasks), "tasks": tasks}


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_task(
    payload: CreateTaskPayload,
    user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """Manually or programmatically create a staff action task."""
    verify_store_access(user, payload.storeId)
    task = await data_client.create_task(payload.model_dump())
    return task


@router.post("/{task_id}/assign", status_code=status.HTTP_200_OK)
async def assign_task(
    task_id: str,
    payload: AssignTaskPayload,
    user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """Assign a task to a store associate."""
    result = await data_client.assign_task(task_id=task_id, user_id=payload.assignedUserId)
    return result


@router.post("/{task_id}/complete", status_code=status.HTTP_200_OK)
async def complete_task(
    task_id: str,
    payload: CompleteTaskPayload,
    user: AuthenticatedUser = Depends(get_current_user),
) -> Dict[str, Any]:
    """Mark a task as resolved with staff resolution notes."""
    result = await data_client.complete_task(task_id=task_id, notes=payload.resolutionNotes)
    return result
