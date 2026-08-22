"""把数据库来源安全同步为已确认名单，同时保留旧来源与历史条目。"""
import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import Source
from app.models.enums import CredibilityLevel, SourceType


_SEED_PATH = Path(__file__).resolve().parent.parent / "core" / "seed_sources.json"


def _load_desired_sources() -> list[dict]:
    return json.loads(_SEED_PATH.read_text(encoding="utf-8"))


def reconcile_sources(db: Session) -> dict[str, int]:
    """停用旧来源并 upsert 当前名单；不删除 Source 或 SourceItem。"""
    desired = _load_desired_sources()
    existing = db.query(Source).order_by(Source.id).all()
    originally_enabled_ids = {source.id for source in existing if source.enabled}
    claimed_ids: set[int] = set()
    created = 0
    reused = 0

    try:
        for source in existing:
            source.enabled = False

        for spec in desired:
            source = next(
                (
                    candidate
                    for candidate in existing
                    if candidate.id not in claimed_ids and candidate.url == spec["url"]
                ),
                None,
            )
            if source is None:
                source = next(
                    (
                        candidate
                        for candidate in existing
                        if candidate.id not in claimed_ids and candidate.name == spec["name"]
                    ),
                    None,
                )

            if source is None:
                source = Source(
                    name=spec["name"],
                    type=SourceType(spec["type"]),
                    url=spec["url"],
                    enabled=bool(spec["enabled"]),
                    credibility_level=CredibilityLevel(spec["credibility_level"]),
                    max_items_per_day=int(spec["max_items_per_day"]),
                )
                db.add(source)
                db.flush()
                existing.append(source)
                created += 1
            else:
                reused += 1

            source.name = spec["name"]
            source.type = SourceType(spec["type"])
            source.url = spec["url"]
            source.enabled = bool(spec["enabled"])
            source.credibility_level = CredibilityLevel(spec["credibility_level"])
            source.max_items_per_day = int(spec["max_items_per_day"])
            claimed_ids.add(source.id)

        db.commit()
    except Exception:
        db.rollback()
        raise

    enabled_count = sum(1 for source in existing if source.id in claimed_ids and source.enabled)
    disabled_legacy = sum(
        1
        for source in existing
        if source.id not in claimed_ids and source.id in originally_enabled_ids
    )
    return {
        "desired": len(desired),
        "created": created,
        "reused": reused,
        "enabled": enabled_count,
        "disabled_legacy": disabled_legacy,
        "total_records": len(existing),
    }
