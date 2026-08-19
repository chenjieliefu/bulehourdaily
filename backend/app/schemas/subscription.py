"""订阅接口结构。"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import PriceType, SubscriptionStatus


class SubscriptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    price_type: PriceType
    monthly_price: int
    status: SubscriptionStatus
    started_at: datetime
    expires_at: datetime


class SubscriptionCreate(BaseModel):
    """运营者人工开通订阅。months 月数；不传 price_type 时按创始价判定。"""
    user_id: int
    months: int = Field(default=1, ge=1, le=12)
    price_type: PriceType | None = None
