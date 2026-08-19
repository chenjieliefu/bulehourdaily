"""采集编排：逐源采集、去重入库、记录运行状态。

关键约束：
- 单一信息源失败不阻断其他来源。
- 相同规范化 URL 只入库一次（确定性去重）。
- 每次运行可追踪到具体信息源与失败时间。
"""
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.time import utcnow
from app.models import CollectionRun, Source, SourceItem
from app.models.enums import CollectionStatus
from app.schemas.collect import CollectRunSummary, SourceRunResult
from .collectors import fetch_items
from .url_normalize import url_hash


def collect_source(db: Session, source: Source) -> SourceRunResult:
    started = utcnow()
    run = CollectionRun(source_id=source.id, status=CollectionStatus.running, started_at=started)
    db.add(run)
    db.commit()
    db.refresh(run)

    try:
        items = fetch_items(source.type, source.url)
    except Exception as exc:  # 单一源失败不阻断整体
        run.status = CollectionStatus.failed
        run.finished_at = utcnow()
        run.error_message = str(exc)[:2000]
        db.commit()
        return SourceRunResult(
            source_id=source.id,
            source_name=source.name,
            status=CollectionStatus.failed,
            items_count=0,
            error_message=str(exc)[:2000],
        )

    new_count = 0
    for it in items:
        h = url_hash(it["url"])
        exists = db.query(SourceItem.id).filter(SourceItem.url_hash == h).first()
        if exists:
            continue
        db.add(
            SourceItem(
                source_id=source.id,
                title=it["title"],
                body=it["body"],
                author=it["author"],
                url=it["url"],
                url_hash=h,
                published_at=it["published_at"],
                raw=it["raw"],
            )
        )
        new_count += 1

    run.status = CollectionStatus.success
    run.finished_at = utcnow()
    run.items_count = new_count
    db.commit()

    return SourceRunResult(
        source_id=source.id,
        source_name=source.name,
        status=CollectionStatus.success,
        items_count=new_count,
    )


def collect_all(db: Session) -> CollectRunSummary:
    started = utcnow()
    sources = db.query(Source).filter(Source.enabled.is_(True)).all()

    results: list[SourceRunResult] = []
    success = 0
    failed = 0
    new_items = 0
    for source in sources:
        r = collect_source(db, source)
        results.append(r)
        if r.status == CollectionStatus.success:
            success += 1
        else:
            failed += 1
        new_items += r.items_count

    return CollectRunSummary(
        started_at=started,
        finished_at=utcnow(),
        total_sources=len(sources),
        success=success,
        failed=failed,
        new_items=new_items,
        results=results,
    )
