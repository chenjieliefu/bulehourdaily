"""订阅测试。"""
from app.models import InviteCode
from app.models.enums import PriceType
from app.services.auth import register
from app.services.subscriptions import create_subscription, has_active_subscription


def _user(db):
    db.add(InviteCode(code="C1"))
    db.commit()
    return register(db, "a@b.com", "secret123", "C1")


def test_create_founding_subscription(db):
    user = _user(db)
    sub = create_subscription(db, user.id)
    assert sub.monthly_price == 29  # 前 50 位创始价
    assert sub.price_type == PriceType.founding
    assert has_active_subscription(db, user.id)


def test_create_standard_subscription(db):
    user = _user(db)
    sub = create_subscription(db, user.id, price_type=PriceType.standard)
    assert sub.monthly_price == 49
    assert sub.price_type == PriceType.standard


def test_no_subscription_by_default(db):
    user = _user(db)
    assert not has_active_subscription(db, user.id)
