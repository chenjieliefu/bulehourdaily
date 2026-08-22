"""清空本地旧内容流水，保留账号资料和已确认的新来源名单。"""
import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import (
    CollectionRun,
    CreationPlan,
    DailyReport,
    EventEvidence,
    HotBrief,
    HotEvent,
    Job,
    MailDelivery,
    PersonalizedReport,
    PersonalizedTopic,
    Source,
    SourceItem,
    TopicFeedback,
    TopicRecommendation,
)


_SEED_PATH = Path(__file__).resolve().parent.parent / "core" / "seed_sources.json"


def _desired_source_names() -> list[str]:
    data = json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    return [source["name"] for source in data]


def reset_local_content(db: Session) -> dict[str, int]:
    """事务清理内容链与旧来源；不会查询或修改 User 等保留表。"""
    desired_names = _desired_source_names()
    desired_sources = db.query(Source).filter(Source.name.in_(desired_names)).all()
    if len(desired_sources) != len(desired_names):
        raise RuntimeError("新来源名单不完整或存在重名，拒绝执行内容清零")
    if {source.name for source in desired_sources} != set(desired_names):
        raise RuntimeError("新来源名单与数据库不一致，拒绝执行内容清零")

    keep_source_ids = {source.id for source in desired_sources}
    deleted: dict[str, int] = {}
    try:
        # 先删最下游引用，再删其父记录，避免破坏外键完整性。
        deletion_order = [
            ("topic_feedback", TopicFeedback),
            ("creation_plan", CreationPlan),
            ("mail_delivery", MailDelivery),
            ("personalized_topic", PersonalizedTopic),
            ("topic_recommendation", TopicRecommendation),
            ("hot_brief", HotBrief),
            ("event_evidence", EventEvidence),
            ("personalized_report", PersonalizedReport),
            ("daily_report", DailyReport),
            ("hot_event", HotEvent),
            ("job", Job),
            ("collection_run", CollectionRun),
            ("source_item", SourceItem),
        ]
        for label, model in deletion_order:
            deleted[label] = db.query(model).delete(synchronize_session=False)

        legacy_deleted = (
            db.query(Source)
            .filter(Source.id.notin_(keep_source_ids))
            .delete(synchronize_session=False)
        )
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "sources_kept": len(keep_source_ids),
        "legacy_sources_deleted": legacy_deleted,
        "content_rows_deleted": sum(deleted.values()),
        **deleted,
    }
