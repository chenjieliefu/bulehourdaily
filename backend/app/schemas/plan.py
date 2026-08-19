"""创作方案接口结构。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    topic_id: int
    core_viewpoint: str
    hooks: list[str] = []
    structure: str
    visual: str
    titles: list[str] = []
    risks: str
    created_at: datetime
