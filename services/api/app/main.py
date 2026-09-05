"""Retail Intelligencia Device Gateway & Backend API.

Entrypoint for FastAPI application.
Handles device event ingestion, registration, store data queries,
and coordinates with the TypeScript Data Service.
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1 import api_v1_router
from app.mqtt.consumer import mqtt_consumer
from app.realtime.broadcaster import broadcaster

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("api.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan managing background services."""
    logger.info(f"Starting {settings.project_name} v{settings.version} in '{settings.environment}' environment...")
    
    # Initialize realtime broadcaster with event loop
    loop = asyncio.get_running_loop()
    broadcaster.set_loop(loop)
    
    # Start MQTT consumer in background if enabled
    mqtt_consumer.start(loop)

    yield

    logger.info("Shutting down background services...")
    mqtt_consumer.stop()
    logger.info("Application shutdown complete.")


app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    description="Physical AI Edge Gateway & Enterprise Retail Intelligence Platform API",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root Health & Readiness Endpoints
@app.get("/health", tags=["Health"], status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, Any]:
    return {
        "status": "HEALTHY",
        "service": "fastapi-gateway",
        "version": settings.version,
        "environment": settings.environment,
        "mqttConnected": mqtt_consumer.is_connected,
    }


@app.get("/ready", tags=["Health"], status_code=status.HTTP_200_OK)
async def readiness_check() -> Dict[str, Any]:
    return {
        "status": "READY",
        "dataServiceConfigured": bool(settings.data_service_url),
    }


# Mount API v1 Routes
app.include_router(api_v1_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
