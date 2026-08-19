"""创作者画像接口。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import CreatorProfile, User
from app.schemas.profile import ProfileRead, ProfileUpdate
from app.services.auth import get_current_user

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=ProfileRead | None)
def get_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(CreatorProfile).filter(CreatorProfile.user_id == user.id).first()
    if profile is None:
        return None
    return profile


@router.put("", response_model=ProfileRead)
def upsert_profile(
    payload: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(CreatorProfile).filter(CreatorProfile.user_id == user.id).first()
    if profile is None:
        profile = CreatorProfile(user_id=user.id, **payload.model_dump())
        db.add(profile)
    else:
        for key, value in payload.model_dump().items():
            setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return profile
