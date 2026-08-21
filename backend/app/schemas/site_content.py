"""结构化站点内容接口。"""
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


SiteContentKey = Literal["product_intro", "membership"]


class SiteContentDraftUpdate(BaseModel):
    content: dict


class SiteContentOperationsRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: SiteContentKey
    draft: dict
    published: dict
    previous_published: dict | None
    updated_at: datetime
    published_at: datetime | None


class SiteContentPublicRead(BaseModel):
    key: SiteContentKey
    content: dict
    published_at: datetime | None
