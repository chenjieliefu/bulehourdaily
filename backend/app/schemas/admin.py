"""质检与邀请码接口结构。"""
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import CredibilityLabel, ReportStatus
from .event import EvidenceItem


class TopicEdit(BaseModel):
    title: str | None = Field(default=None, max_length=300)
    what_happened: str | None = None
    why_now: str | None = None
    angle: str | None = None
    hook: str | None = None
    structure: str | None = None
    visual: str | None = None
    time_window: str | None = None


class ReviewTopic(BaseModel):
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
    reviewed: bool
    evidence: list[EvidenceItem] = []


class CandidateEvent(BaseModel):
    id: int
    title: str
    summary: str
    credibility_label: CredibilityLabel
    sort_score: float
    evidence_count: int


class ReviewPayload(BaseModel):
    report_id: int | None
    report_date: date | None
    status: ReportStatus | None
    summary: str | None
    published_at: datetime | None
    topics: list[ReviewTopic] = []
    candidates: list[CandidateEvent] = []


class AddTopicRequest(BaseModel):
    event_id: int


class InviteCodeCreate(BaseModel):
    count: int = Field(default=5, ge=1, le=100)


class InviteCodeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    used: bool
    used_at: datetime | None
