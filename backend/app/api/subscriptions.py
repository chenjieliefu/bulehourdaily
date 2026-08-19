"""订阅接口：查看我的订阅 + 运营者人工开通。"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Subscription, User
from app.models.enums import SubscriptionStatus
from app.schemas.subscription import SubscriptionCreate, SubscriptionRead
from app.services.auth import get_current_user
from app.services.subscriptions import create_subscription, has_active_subscription

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.get("/me", response_model=SubscriptionRead | None)
def my_subscription(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not has_active_subscription(db, user.id):
        return None
    sub = (
        db.query(Subscription)
        .filter(
            Subscription.user_id == user.id,
            Subscription.status == SubscriptionStatus.active,
        )
        .order_by(Subscription.expires_at.desc())
        .first()
    )
    return sub


@router.post("", response_model=SubscriptionRead, status_code=201)
def operator_create(payload: SubscriptionCreate, db: Session = Depends(get_db)):
    """运营者人工开通（MVP 本地直调，正式运营后台在阶段 6）。"""
    user = db.get(User, payload.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return create_subscription(db, payload.user_id, payload.months, payload.price_type)
