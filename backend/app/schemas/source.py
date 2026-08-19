"""信息源接口结构。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import CredibilityLevel, SourceType


class SourceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    type: SourceType
    url: str = Field(min_length=1, max_length=1000)
    enabled: bool = True
    credibility_level: CredibilityLevel = CredibilityLevel.official
    max_items_per_day: int = Field(default=3, ge=1, le=20)


class SourceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    type: SourceType | None = None
    url: str | None = Field(default=None, min_length=1, max_length=1000)
    enabled: bool | None = None
    credibility_level: CredibilityLevel | None = None
    max_items_per_day: int | None = Field(default=None, ge=1, le=20)


class SourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    type: SourceType
    url: str
    enabled: bool
    credibility_level: CredibilityLevel
    max_items_per_day: int
    created_at: datetime
    updated_at: datetime
