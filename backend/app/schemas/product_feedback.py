"""产品意见反馈接口结构。"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


FeedbackCategory = Literal[
    "bug",
    "content",
    "experience",
    "membership",
    "suggestion",
    "other",
]


class ProductFeedbackCreate(BaseModel):
    category: FeedbackCategory
    content: str = Field(min_length=5, max_length=2000)
    contact_email: str | None = Field(default=None, max_length=320)
    page_url: str | None = Field(default=None, max_length=1000)

    @field_validator("content")
    @classmethod
    def clean_content(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 5:
            raise ValueError("反馈内容至少需要 5 个字")
        return value

    @field_validator("contact_email")
    @classmethod
    def clean_email(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        value = value.strip().lower()
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            raise ValueError("联系邮箱格式不正确")
        return value

    @field_validator("page_url")
    @classmethod
    def clean_page_url(cls, value: str | None) -> str | None:
        return value.strip() if value and value.strip() else None


class ProductFeedbackRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: str
    status: str
    created_at: datetime
