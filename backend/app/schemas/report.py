"""通用日报接口结构。"""
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import CredibilityLabel, ReportStatus
from .event import EvidenceItem


class TopicRead(BaseModel):
    id: int
    title: str
    what_happened: str
    why_now: str
    angle: str
    hook: str
    structure: str
    visual: str
    time_window: str
    order_index: int
    hot_event_id: int
    credibility_label: CredibilityLabel | None = None
    event_published_at: datetime | None = None
    evidence: list[EvidenceItem] = []


class BriefRead(BaseModel):
    id: int
    summary: str
    order_index: int
    hot_event_id: int
    event_published_at: datetime | None = None
    evidence: list[EvidenceItem] = []


class ReportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    report_date: date
    status: ReportStatus
    summary: str | None
    published_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ReportDetail(ReportRead):
    last_collect_at: datetime | None = None
    topics: list[TopicRead] = []
    briefs: list[BriefRead] = []
