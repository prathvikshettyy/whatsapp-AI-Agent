from typing import List
from pydantic import BaseModel


class DailyVolumeItem(BaseModel):
    date: str
    user_messages: int
    bot_replies: int


class AnalyticsResponse(BaseModel):
    total_conversations: int
    messages_today: int
    handoff_rate: float
    avg_response_time_sec: float
    bot_resolution_rate: float
    estimated_token_cost_usd: float
    daily_volume: List[DailyVolumeItem]
