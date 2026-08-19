"""发布反馈接口结构。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import FeedbackStatus


class FeedbackUpdate(BaseModel):
    status: FeedbackStatus
    douyin_url: str | None = Field(default=None, max_length=1000)


class FeedbackRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    topic_id: int
    status: FeedbackStatus
    douyin_url: str | None
    updated_at: datetime
