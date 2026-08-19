"""订阅：人工开通、资格判断。无自动支付。"""
from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.time import utcnow
from app.models import Subscription
from app.models.enums import PriceType, SubscriptionStatus

FOUNDING_PRICE = 29
STANDARD_PRICE = 49
FOUNDING_LIMIT = 50  # 前 50 位创始订阅


def has_active_subscription(db: Session, user_id: int) -> bool:
    now = utcnow()
    return (
        db.query(Subscription)
        .filter(
            Subscription.user_id == user_id,
            Subscription.status == SubscriptionStatus.active,
            Subscription.expires_at > now,
        )
        .first()
        is not None
    )


def create_subscription(db: Session, user_id: int, months: int = 1, price_type: PriceType | None = None) -> Subscription:
    if price_type is None:
        founding_count = (
            db.query(Subscription).filter(Subscription.price_type == PriceType.founding).count()
        )
        price_type = PriceType.founding if founding_count < FOUNDING_LIMIT else PriceType.standard

    price = FOUNDING_PRICE if price_type == PriceType.founding else STANDARD_PRICE
    started = utcnow()
    expires = started + timedelta(days=30 * months)

    sub = Subscription(
        user_id=user_id,
        price_type=price_type,
        monthly_price=price,
        status=SubscriptionStatus.active,
        started_at=started,
        expires_at=expires,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return sub
