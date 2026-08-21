"""站点内容草稿、发布与回滚。"""
from copy import deepcopy

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.time import utcnow
from app.models import SiteContent


DEFAULT_SITE_CONTENT: dict[str, dict] = {
    "product_intro": {
        "eyebrow": "Blue Hour Daily · 08:00",
        "title": "在世界醒来之前，看见下一刻。",
        "subtitle": "每天 08:00，把海外最新 AI 动态，变成三个值得拍的抖音选题。",
        "section_title": "每天一份日报，把「看信息」变成「拍什么」。",
        "features": [
            {"title": "不漏掉", "detail": "盯着 40 多个海外 AI 信息源，每天 08:00 汇总最新动态。"},
            {"title": "会判断", "detail": "聚成热点事件，标注可信度，告诉你哪个值得跟进。"},
            {"title": "能行动", "detail": "每个选题给出钩子、结构、画面建议，直接开拍。"},
        ],
    },
    "membership": {
        "title": "升级会员",
        "subtitle": "通用日报看今天，个性化日报看「适合我的今天」。",
        "hero_title": "少刷一小时信息流，每天多一个可以开拍的选题。",
        "hero_detail": "会员不是给你更多资讯，而是基于你的账号画像，把当天真正适合你的热点转成可行动的创作方案。",
        "trial_title": "注册后免费获得 3 份个性化日报",
        "trial_detail": "体验按成功生成的日报份数计算，不绑定支付方式。体验结束后仍可继续阅读公开日报。",
    },
}


def get_or_create(db: Session, key: str) -> SiteContent:
    if key not in DEFAULT_SITE_CONTENT:
        raise ValueError("不支持的站点内容")
    row = db.query(SiteContent).filter(SiteContent.key == key).first()
    if row is None:
        content = deepcopy(DEFAULT_SITE_CONTENT[key])
        row = SiteContent(key=key, draft=content, published=deepcopy(content), published_at=utcnow())
        db.add(row)
        try:
            db.commit()
            db.refresh(row)
        except IntegrityError:
            # 首次读取可能被浏览器并发触发；唯一键保证只保留一个默认版本。
            db.rollback()
            row = db.query(SiteContent).filter(SiteContent.key == key).one()
    return row


def save_draft(db: Session, key: str, content: dict) -> SiteContent:
    row = get_or_create(db, key)
    row.draft = deepcopy(content)
    db.commit()
    db.refresh(row)
    return row


def publish(db: Session, key: str) -> SiteContent:
    row = get_or_create(db, key)
    row.previous_published = deepcopy(row.published)
    row.published = deepcopy(row.draft)
    row.published_at = utcnow()
    db.commit()
    db.refresh(row)
    return row


def rollback(db: Session, key: str) -> SiteContent:
    row = get_or_create(db, key)
    if row.previous_published is None:
        raise ValueError("没有可恢复的上一个版本")
    current = deepcopy(row.published)
    row.published = deepcopy(row.previous_published)
    row.draft = deepcopy(row.published)
    row.previous_published = current
    row.published_at = utcnow()
    db.commit()
    db.refresh(row)
    return row
