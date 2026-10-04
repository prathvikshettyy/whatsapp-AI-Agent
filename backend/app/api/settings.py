"""Settings and prompt versioning endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import settings as app_settings
from backend.app.db import get_db
from backend.app.models.audit_log import AuditLog
from backend.app.models.setting import Setting
from backend.app.schemas.setting import SettingResponse, SettingUpdate

settings_router = APIRouter(prefix="/settings", tags=["settings"])


@settings_router.get("", response_model=SettingResponse)
async def get_latest_settings(db: AsyncSession = Depends(get_db)):
    stmt = select(Setting).order_by(desc(Setting.version)).limit(1)
    res = await db.execute(stmt)
    latest = res.scalar_one_or_none()

    if not latest:
        # Seed initial setting row
        latest = Setting(
            system_prompt=(
                "You are an intelligent customer support AI assistant communicating with users on WhatsApp.\n"
                "Never use Markdown headers or tables because WhatsApp does not support them."
            ),
            model=app_settings.CLAUDE_MODEL,
            rate_limit_per_min=app_settings.RATE_LIMIT_PER_MIN,
            handoff_keyword="agent",
            version=1,
            created_by="System",
        )
        db.add(latest)
        await db.commit()
        await db.refresh(latest)

    return latest


@settings_router.put("", response_model=SettingResponse)
async def update_settings(update: SettingUpdate, db: AsyncSession = Depends(get_db)):
    stmt = select(Setting).order_by(desc(Setting.version)).limit(1)
    res = await db.execute(stmt)
    current = res.scalar_one_or_none()

    next_version = (current.version + 1) if current else 1

    new_setting = Setting(
        system_prompt=update.system_prompt or (current.system_prompt if current else ""),
        model=update.model or (current.model if current else app_settings.CLAUDE_MODEL),
        rate_limit_per_min=update.rate_limit_per_min or (current.rate_limit_per_min if current else 10),
        handoff_keyword=update.handoff_keyword or (current.handoff_keyword if current else "agent"),
        version=next_version,
        created_by="Staff Admin",
    )
    db.add(new_setting)
    db.add(AuditLog(action="settings_update", meta={"version": next_version, "summary": update.version_summary}))
    await db.commit()
    await db.refresh(new_setting)

    # Sync to live app settings
    if update.model:
        app_settings.CLAUDE_MODEL = update.model
    if update.rate_limit_per_min:
        app_settings.RATE_LIMIT_PER_MIN = update.rate_limit_per_min

    return new_setting


@settings_router.get("/prompt-history", response_model=list[SettingResponse])
async def get_prompt_history(db: AsyncSession = Depends(get_db)):
    stmt = select(Setting).order_by(desc(Setting.version)).limit(20)
    res = await db.execute(stmt)
    return res.scalars().all()
