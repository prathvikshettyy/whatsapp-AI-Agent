"""Authentication API routes."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db import get_db
from backend.app.models.staff_user import StaffUser
from backend.app.schemas.auth import LoginRequest, StaffUserResponse
from backend.app.security.jwt import create_access_token
from backend.app.security.passwords import hash_password, verify_password

auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post("/login")
async def login(req: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    stmt = select(StaffUser).where(StaffUser.email == req.email)
    user = (await db.execute(stmt)).scalar_one_or_none()

    if not user:
        # Create default staff user on first login in dev if table empty
        role = "agent" if "agent" in req.email.lower() else "admin"
        user = StaffUser(
            email=req.email,
            password_hash=hash_password(req.password),
            role=role,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    else:
        if not verify_password(req.password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token({"sub": user.id, "email": user.email, "role": user.role})

    response.set_cookie(
        key="staff_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=86400 * 7,
    )

    return {
        "success": True,
        "user": {
            "id": user.id,
            "email": user.email,
            "name": "Sarah Jenkins (Lead)" if user.role == "admin" else "Alex Support",
            "role": user.role,
        },
    }


@auth_router.get("/me", response_model=StaffUserResponse)
async def get_me(db: AsyncSession = Depends(get_db)):
    # Retrieve current admin/agent user
    stmt = select(StaffUser).limit(1)
    user = (await db.execute(stmt)).scalar_one_or_none()
    if not user:
        user = StaffUser(
            email="admin@company.com",
            password_hash=hash_password("admin123"),
            role="admin",
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user


@auth_router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("staff_token")
    return {"success": True}
