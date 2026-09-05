"""API v1 master router mounting all sub-routes."""
from fastapi import APIRouter

from app.api.v1.events import router as events_router
from app.api.v1.devices import router as devices_router
from app.api.v1.stores import router as stores_router
from app.api.v1.alerts import router as alerts_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.realtime import router as realtime_router

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(events_router)
api_v1_router.include_router(devices_router)
api_v1_router.include_router(stores_router)
api_v1_router.include_router(alerts_router)
api_v1_router.include_router(tasks_router)
api_v1_router.include_router(analytics_router)
api_v1_router.include_router(realtime_router)

__all__ = ["api_v1_router"]
