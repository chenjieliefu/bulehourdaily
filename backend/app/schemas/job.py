"""任务接口结构。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import JobKind, JobStatus


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: JobKind
    status: JobStatus
    result_ref: str | None
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
