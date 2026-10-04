from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class SettingUpdate(BaseModel):
    system_prompt: Optional[str] = None
    model: Optional[str] = None
    rate_limit_per_min: Optional[int] = None
    handoff_keyword: Optional[str] = None
    version_summary: Optional[str] = None


class SettingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    system_prompt: str
    model: str
    rate_limit_per_min: int
    handoff_keyword: str
    version: int
    created_by: str
    created_at: datetime
