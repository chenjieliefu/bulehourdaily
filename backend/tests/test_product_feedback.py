"""产品意见反馈测试。"""
import pytest
from pydantic import ValidationError

from app.models import ProductFeedback
from app.schemas.product_feedback import ProductFeedbackCreate
from app.services.product_feedback import create_product_feedback


def test_create_anonymous_product_feedback(db):
    payload = ProductFeedbackCreate(
        category="suggestion",
        content="希望归档列表可以增加日期筛选。",
        contact_email=" User@Example.com ",
        page_url="https://example.com/archive",
    )

    created = create_product_feedback(db, payload)

    assert created.id is not None
    assert created.user_id is None
    assert created.contact_email == "user@example.com"
    assert created.status == "new"
    assert db.query(ProductFeedback).count() == 1


def test_product_feedback_rejects_too_short_content():
    with pytest.raises(ValidationError):
        ProductFeedbackCreate(category="bug", content="短")


def test_product_feedback_rejects_invalid_email():
    with pytest.raises(ValidationError):
        ProductFeedbackCreate(
            category="bug",
            content="页面上的按钮无法点击。",
            contact_email="not-an-email",
        )
