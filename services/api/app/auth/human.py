"""Human user authentication and Role-Based Access Control (RBAC)."""
from fastapi import Header, HTTPException, status
from typing import Optional


class AuthenticatedUser:
    def __init__(self, user_id: str, email: str, role: str, store_id: Optional[str] = None):
        self.user_id = user_id
        self.email = email
        self.role = role
        self.store_id = store_id


async def get_current_user(
    authorization: Optional[str] = Header(None),
) -> AuthenticatedUser:
    """Dependency extracting human user identity and role."""
    if not authorization:
        # Default development user: Store Manager for store_001
        return AuthenticatedUser(
            user_id="usr_mgr_001",
            email="manager@retail-intelligencia.io",
            role="STORE_MANAGER",
            store_id="store_001",
        )

    parts = authorization.split(" ")
    token = parts[1] if len(parts) == 2 else authorization

    if "admin" in token.lower():
        return AuthenticatedUser(
            user_id="usr_admin_001",
            email="admin@retail-intelligencia.io",
            role="PLATFORM_ADMIN",
            store_id=None,
        )
    elif "staff" in token.lower():
        return AuthenticatedUser(
            user_id="usr_staff_102",
            email="staff@retail-intelligencia.io",
            role="STORE_STAFF",
            store_id="store_001",
        )
    else:
        return AuthenticatedUser(
            user_id="usr_mgr_001",
            email="manager@retail-intelligencia.io",
            role="STORE_MANAGER",
            store_id="store_001",
        )


def verify_store_access(user: AuthenticatedUser, store_id: str) -> None:
    """Enforce strict multi-tenant horizontal isolation."""
    if user.role == "PLATFORM_ADMIN":
        return
    if user.store_id != store_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": {
                    "code": "CROSS_STORE_ACCESS_DENIED",
                    "message": f"User from store '{user.store_id}' is forbidden from accessing store '{store_id}'.",
                }
            },
        )
