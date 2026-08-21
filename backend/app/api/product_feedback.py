"""产品意见反馈接口。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import User
from app.schemas.product_feedback import ProductFeedbackCreate, ProductFeedbackRead
from app.services.auth import get_optional_current_user
from app.services.product_feedback import create_product_feedback

router = APIRouter(prefix="/product-feedback", tags=["product-feedback"])


@router.post("", response_model=ProductFeedbackRead, status_code=201)
def submit_product_feedback(
    payload: ProductFeedbackCreate,
    user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
):
    return create_product_feedback(db, payload, user.id if user else None)
