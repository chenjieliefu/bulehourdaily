"""首次启动时写入种子信息源（幂等：已有数据则跳过）。"""
import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import InviteCode, Source
from app.models.enums import CredibilityLevel, SourceType

_SEED_PATH = Path(__file__).resolve().parent.parent / "core" / "seed_sources.json"


def seed_sources(db: Session) -> int:
    """返回本次写入的源数量；若已存在任何源则返回 0（不重复写入）。"""
    if db.query(Source.id).first() is not None:
        return 0

    data = json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    count = 0
    for s in data:
        db.add(
            Source(
                name=s["name"],
                type=SourceType(s["type"]),
                url=s["url"],
                enabled=s["enabled"],
                credibility_level=CredibilityLevel(s["credibility_level"]),
                max_items_per_day=s["max_items_per_day"],
            )
        )
        count += 1
    db.commit()
    return count


def seed_invite_codes(db: Session) -> int:
    """首次启动写入几个测试邀请码（体验用）；已有则不重复。"""
    if db.query(InviteCode.id).first() is not None:
        return 0
    for c in ["WEILAN001", "WEILAN002", "WEILAN003", "WEILAN004", "WEILAN005"]:
        db.add(InviteCode(code=c))
    db.commit()
    return 5
