"""采集接口结构。"""
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import CollectionStatus, CredibilityLevel, SourceType


class SourceRunResult(BaseModel):
    source_id: int
    source_name: str
    status: CollectionStatus
    items_count: int
    error_message: str | None = None


class CollectRunSummary(BaseModel):
    started_at: datetime
    finished_at: datetime
    total_sources: int
    success: int
    failed: int
    new_items: int
    results: list[SourceRunResult]


class StatusSource(BaseModel):
    source_id: int
    source_name: str
    type: SourceType
    credibility_level: CredibilityLevel
    max_items_per_day: int
    enabled: bool
    last_success_at: datetime | None
    last_status: CollectionStatus | None
    last_error: str | None


class StatusRead(BaseModel):
    last_collect_at: datetime | None
    total_sources: int
    enabled_sources: int
    total_items: int
    sources: list[StatusSource]
