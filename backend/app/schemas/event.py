"""热点事件接口结构。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import CredibilityLabel, EventStatus


class EvidenceItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    source_item_id: int
    title: str
    url: str
    source_name: str
    published_at: datetime | None


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    summary: str
    credibility_label: CredibilityLabel
    relevance_score: int
    actionability_score: int
    freshness_score: int
    sort_score: float
    reason: str | None
    status: EventStatus
    first_seen_at: datetime
    evidence_count: int = 0


class EventDetail(EventRead):
    evidence: list[EvidenceItem] = []
