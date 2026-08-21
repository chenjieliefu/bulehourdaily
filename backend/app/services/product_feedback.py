"""产品意见反馈写入服务。"""
from sqlalchemy.orm import Session

from app.models import ProductFeedback
from app.schemas.product_feedback import ProductFeedbackCreate


def create_product_feedback(
    db: Session,
    payload: ProductFeedbackCreate,
    user_id: int | None = None,
) -> ProductFeedback:
    feedback = ProductFeedback(
        user_id=user_id,
        category=payload.category,
        content=payload.content,
        contact_email=payload.contact_email,
        page_url=payload.page_url,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback
