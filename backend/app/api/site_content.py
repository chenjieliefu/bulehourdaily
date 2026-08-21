"""公开读取已发布的站点文案。草稿管理位于运营接口。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.site_content import SiteContentKey, SiteContentPublicRead
from app.services import site_content as site_content_svc

router = APIRouter(prefix="/site-content", tags=["site-content"])


@router.get("/{key}", response_model=SiteContentPublicRead)
def get_public_site_content(key: SiteContentKey, db: Session = Depends(get_db)):
    row = site_content_svc.get_or_create(db, key)
    return {"key": row.key, "content": row.published, "published_at": row.published_at}
