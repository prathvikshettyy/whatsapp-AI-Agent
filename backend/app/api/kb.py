"""Knowledge base CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.db import get_db
from backend.app.models.kb_doc import KbDoc
from backend.app.schemas.kb import KbDocCreate, KbDocResponse, KbDocUpdate

kb_router = APIRouter(prefix="/kb", tags=["kb"])


@kb_router.get("", response_model=list[KbDocResponse])
async def list_kb(db: AsyncSession = Depends(get_db)):
    stmt = select(KbDoc).order_by(KbDoc.updated_at.desc())
    res = await db.execute(stmt)
    return res.scalars().all()


@kb_router.post("", response_model=KbDocResponse)
async def create_kb_doc(doc: KbDocCreate, db: AsyncSession = Depends(get_db)):
    item = KbDoc(title=doc.title, body=doc.body)
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return item


@kb_router.put("/{doc_id}", response_model=KbDocResponse)
async def update_kb_doc(doc_id: str, doc: KbDocUpdate, db: AsyncSession = Depends(get_db)):
    stmt = select(KbDoc).where(KbDoc.id == doc_id)
    item = (await db.execute(stmt)).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Document not found")

    if doc.title:
        item.title = doc.title
    if doc.body:
        item.body = doc.body

    await db.commit()
    await db.refresh(item)
    return item


@kb_router.delete("/{doc_id}")
async def delete_kb_doc(doc_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(KbDoc).where(KbDoc.id == doc_id)
    item = (await db.execute(stmt)).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Document not found")
    await db.delete(item)
    await db.commit()
    return {"success": True}
