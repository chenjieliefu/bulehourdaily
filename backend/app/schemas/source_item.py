"""来源条目接口结构。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SourceItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_id: int
    title: str
    body: str | None
    author: str | None
    url: str
    published_at: datetime | None
    collected_at: datetime
