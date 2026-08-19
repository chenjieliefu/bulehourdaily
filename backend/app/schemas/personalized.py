"""个性化日报接口结构。"""
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import CredibilityLabel, FeedbackStatus
from .event import EvidenceItem


class PersonalizedTopicRead(BaseModel):
    id: int
    title: str
    what_happened: str
    why_now: str
    angle: str
    hook: str
    structure: str
    visual: str
    time_window: str
    recommendation_reason: str
    order_index: int
    hot_event_id: int
    credibility_label: CredibilityLabel | None = None
    event_published_at: datetime | None = None
    evidence: list[EvidenceItem] = []
    feedback_status: FeedbackStatus | None = None
    feedback_douyin_url: str | None = None


class PersonalizedReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    report_date: date
    summary: str | None
    reason: str | None
    created_at: datetime


class PersonalizedReportDetail(PersonalizedReportRead):
    topics: list[PersonalizedTopicRead] = []
