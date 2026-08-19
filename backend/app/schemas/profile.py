"""创作者画像接口结构。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProfileUpdate(BaseModel):
    positioning: str = Field(min_length=1, max_length=2000)
    audience: str = Field(min_length=1, max_length=2000)
    persona: str = Field(min_length=1, max_length=2000)
    style: str = Field(min_length=1, max_length=2000)
    video_length: str = Field(min_length=1, max_length=200)
    forbidden: str = Field(min_length=1, max_length=2000)


class ProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    positioning: str
    audience: str
    persona: str
    style: str
    video_length: str
    forbidden: str
    updated_at: datetime
