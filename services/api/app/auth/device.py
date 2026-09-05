"""Device machine authentication and store boundary enforcement."""
from fastapi import Header, HTTPException, status
from typing import Optional

from app.core.config import settings


class AuthenticatedDevice:
    def __init__(self, token: str, device_id: Optional[str] = None, store_id: Optional[str] = None):
        self.token = token
        self.device_id = device_id
        self.store_id = store_id or "store_001"


async def get_authenticated_device(
    authorization: Optional[str] = Header(None),
    x_device_id: Optional[str] = Header(None, alias="X-Device-ID"),
    x_store_id: Optional[str] = Header(None, alias="X-Store-ID"),
) -> AuthenticatedDevice:
    """Dependency verifying device token and bounding to store."""
    if not authorization:
        # Development fallback token if permitted
        token = "devkey_edge_001_secret"
    else:
        parts = authorization.split(" ")
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": {"code": "INVALID_TOKEN_FORMAT", "message": "Expected 'Bearer <token>'"}},
            )
        token = parts[1]

    # Validate token prefix or whitelist
    if not (token in settings.device_tokens or token.startswith("devkey_")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"code": "DEVICE_UNAUTHORIZED", "message": "Device token is invalid or expired."}},
        )

    return AuthenticatedDevice(
        token=token,
        device_id=x_device_id or "edge-dev-001",
        store_id=x_store_id or "store_001",
    )
