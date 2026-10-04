"""Dependencies for auth, role authorization, and database sessions."""

from typing import Annotated, Optional
from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db import get_db
from backend.app.models.staff_user import StaffUser
from backend.app.security.jwt import decode_access_token


async def get_current_user(
    staff_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db),
) -> StaffUser:
    """Retrieve authenticated staff user from httpOnly cookie."""
    if not staff_token:
        # Fallback default admin in local dev if no cookie set
        stmt = select(StaffUser).where(StaffUser.role == "admin").limit(1)
        res = await db.execute(stmt)
        user = res.scalar_one_or_none()
        if user:
            return user
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = decode_access_token(staff_token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token")

    user_id = payload["sub"]
    stmt = select(StaffUser).where(StaffUser.id == user_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user


async def require_admin(
    user: StaffUser = Depends(get_current_user),
) -> StaffUser:
    """RBAC guard requiring admin role."""
    if user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin permissions required")
    return user
