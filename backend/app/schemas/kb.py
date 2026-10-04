from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class KbDocCreate(BaseModel):
    title: str
    body: str


class KbDocUpdate(BaseModel):
    title: Optional[str] = None
    body: Optional[str] = None


class KbDocResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    body: str
    updated_at: datetime
