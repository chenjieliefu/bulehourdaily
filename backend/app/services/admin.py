"""运营工作台：日报质检、创作者状态、个性化内容与反馈。"""
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.time import utcnow
from app.models import (
    CreationPlan,
    CreatorProfile,
    DailyReport,
    EventEvidence,
    HotEvent,
    Job,
    MailDelivery,
    PersonalizedReport,
    PersonalizedTopic,
    ProductFeedback,
    SourceItem,
    Subscription,
    TopicFeedback,
    TopicRecommendation,
    User,
)
from app.models.enums import EventStatus, FeedbackStatus, MailStatus, ReportStatus, SubscriptionStatus
from . import llm
from .report_generation import _deadline_str, _hours_ago

_BJ = ZoneInfo("Asia/Shanghai")
_TOPIC_PROMPT = (Path(__file__).resolve().parent / "prompts" / "single_topic.md").read_text(encoding="utf-8")


def _today() -> date:
    return datetime.now(_BJ).date()


def _today_utc_start() -> datetime:
    local_start = datetime.combine(_today(), time.min, tzinfo=_BJ)
    return local_start.astimezone(timezone.utc).replace(tzinfo=None)


def _active_subscription(subscriptions: list[Subscription], now: datetime) -> Subscription | None:
    active = [
        sub
        for sub in subscriptions
        if sub.status == SubscriptionStatus.active and sub.expires_at > now
    ]
    return max(active, key=lambda sub: sub.expires_at) if active else None


def creator_operations_rows(db: Session) -> list[dict]:
    """汇总运营可证明的创作者状态；不把注册时间冒充为活跃时间。"""
    now = utcnow()
    users = db.query(User).filter(User.is_operator.is_(False)).order_by(User.created_at.desc()).all()
    rows: list[dict] = []

    for user in users:
        profile = db.query(CreatorProfile).filter(CreatorProfile.user_id == user.id).first()
        reports = (
            db.query(PersonalizedReport)
            .filter(PersonalizedReport.user_id == user.id)
            .order_by(PersonalizedReport.report_date.desc(), PersonalizedReport.id.desc())
            .all()
        )
        subscriptions = db.query(Subscription).filter(Subscription.user_id == user.id).all()
        active_sub = _active_subscription(subscriptions, now)
        had_subscription = bool(subscriptions)

        if active_sub:
            entitlement_status = "subscriber"
        elif had_subscription:
            entitlement_status = "expired"
        elif len(reports) < settings.trial_personalized_reports:
            entitlement_status = "trial"
        else:
            entitlement_status = "trial_exhausted"

        plans = db.query(CreationPlan).filter(CreationPlan.user_id == user.id).all()
        feedbacks = db.query(TopicFeedback).filter(TopicFeedback.user_id == user.id).all()
        latest_mail = (
            db.query(MailDelivery)
            .filter(MailDelivery.user_id == user.id)
            .order_by(MailDelivery.created_at.desc(), MailDelivery.id.desc())
            .first()
        )
        interaction_times = [report.created_at for report in reports]
        interaction_times.extend(plan.created_at for plan in plans)
        interaction_times.extend(feedback.updated_at for feedback in feedbacks)

        rows.append(
            {
                "id": user.id,
                "email": user.email,
                "created_at": user.created_at,
                "has_profile": profile is not None,
                "profile_positioning": profile.positioning if profile else None,
                "entitlement_status": entitlement_status,
                "trial_remaining": max(0, settings.trial_personalized_reports - len(reports)),
                "subscription_price_type": active_sub.price_type.value if active_sub else None,
                "subscription_monthly_price": active_sub.monthly_price if active_sub else None,
                "subscription_expires_at": active_sub.expires_at if active_sub else None,
                "personalized_report_count": len(reports),
                "last_report_date": reports[0].report_date if reports else None,
                "creation_plan_count": len(plans),
                "feedback_want": sum(f.status == FeedbackStatus.want for f in feedbacks),
                "feedback_not_interested": sum(f.status == FeedbackStatus.not_interested for f in feedbacks),
                "feedback_published": sum(f.status == FeedbackStatus.published for f in feedbacks),
                "latest_mail_status": latest_mail.status.value if latest_mail else None,
                "latest_interaction_at": max(interaction_times) if interaction_times else None,
                "product_feedback_count": db.query(ProductFeedback).filter(ProductFeedback.user_id == user.id).count(),
            }
        )
    return rows


def operations_overview(db: Session) -> dict:
    today = _today()
    now = utcnow()
    rows = creator_operations_rows(db)
    report = db.query(DailyReport).filter(DailyReport.report_date == today).first()
    unreviewed = 0
    if report:
        unreviewed = (
            db.query(TopicRecommendation)
            .filter(
                TopicRecommendation.report_id == report.id,
                TopicRecommendation.reviewed.is_(False),
            )
            .count()
        )

    today_report_users = {
        row.user_id
        for row in db.query(PersonalizedReport.user_id)
        .filter(PersonalizedReport.report_date == today)
        .all()
    }
    eligible_ids = {
        row["id"]
        for row in rows
        if row["entitlement_status"] in {"subscriber", "trial"}
    } | today_report_users
    expiring_at = now + timedelta(days=7)

    return {
        "report_date": today,
        "public_report_status": report.status if report else None,
        "unreviewed_topics": unreviewed,
        "creators_total": len(rows),
        "profiles_completed": sum(row["has_profile"] for row in rows),
        "active_subscribers": sum(row["entitlement_status"] == "subscriber" for row in rows),
        "trial_creators": sum(row["entitlement_status"] == "trial" for row in rows),
        "trial_exhausted": sum(row["entitlement_status"] in {"trial_exhausted", "expired"} for row in rows),
        "expiring_subscribers": sum(
            row["subscription_expires_at"] is not None
            and row["subscription_expires_at"] <= expiring_at
            for row in rows
        ),
        "today_personalized_reports": len(today_report_users),
        "today_personalized_expected": len(eligible_ids),
        "failed_mail_deliveries": db.query(MailDelivery).filter(
            MailDelivery.created_at >= _today_utc_start(),
            MailDelivery.status == MailStatus.failed,
        ).count(),
        "new_product_feedback": db.query(ProductFeedback).filter(ProductFeedback.status == "new").count(),
    }


def personalized_content_rows(
    db: Session,
    user_id: int | None = None,
    report_date: date | None = None,
    limit: int = 50,
) -> list[dict]:
    query = db.query(PersonalizedReport).order_by(
        PersonalizedReport.report_date.desc(), PersonalizedReport.id.desc()
    )
    if user_id is not None:
        query = query.filter(PersonalizedReport.user_id == user_id)
    if report_date is not None:
        query = query.filter(PersonalizedReport.report_date == report_date)
    reports = query.limit(limit).all()
    if not reports:
        return []

    report_ids = [report.id for report in reports]
    topics = (
        db.query(PersonalizedTopic)
        .filter(PersonalizedTopic.report_id.in_(report_ids))
        .order_by(PersonalizedTopic.report_id, PersonalizedTopic.order_index)
        .all()
    )
    topic_ids = [topic.id for topic in topics]
    event_ids = list({topic.hot_event_id for topic in topics})
    users = {user.id: user for user in db.query(User).filter(User.id.in_([r.user_id for r in reports])).all()}
    events = {event.id: event for event in db.query(HotEvent).filter(HotEvent.id.in_(event_ids)).all()} if event_ids else {}
    plans = {plan.topic_id: plan for plan in db.query(CreationPlan).filter(CreationPlan.topic_id.in_(topic_ids)).all()} if topic_ids else {}
    feedbacks = {feedback.topic_id: feedback for feedback in db.query(TopicFeedback).filter(TopicFeedback.topic_id.in_(topic_ids)).all()} if topic_ids else {}
    deliveries = (
        db.query(MailDelivery)
        .filter(MailDelivery.report_id.in_(report_ids))
        .order_by(MailDelivery.created_at.desc(), MailDelivery.id.desc())
        .all()
    )
    latest_delivery: dict[int, MailDelivery] = {}
    for delivery in deliveries:
        if delivery.report_id is not None:
            latest_delivery.setdefault(delivery.report_id, delivery)

    evidence_map: dict[int, list[dict]] = {}
    if event_ids:
        evidence_rows = db.query(EventEvidence).filter(EventEvidence.hot_event_id.in_(event_ids)).all()
        item_ids = [row.source_item_id for row in evidence_rows]
        items = {item.id: item for item in db.query(SourceItem).filter(SourceItem.id.in_(item_ids)).all()}
        for row in evidence_rows:
            item = items.get(row.source_item_id)
            if item:
                evidence_map.setdefault(row.hot_event_id, []).append(
                    {
                        "source_item_id": item.id,
                        "title": item.title,
                        "url": item.url,
                        "source_name": item.source.name,
                        "published_at": item.published_at,
                    }
                )

    topics_by_report: dict[int, list[dict]] = {}
    for topic in topics:
        plan = plans.get(topic.id)
        feedback = feedbacks.get(topic.id)
        event = events.get(topic.hot_event_id)
        topics_by_report.setdefault(topic.report_id, []).append(
            {
                "id": topic.id,
                "order_index": topic.order_index,
                "title": topic.title,
                "what_happened": topic.what_happened,
                "why_now": topic.why_now,
                "angle": topic.angle,
                "hook": topic.hook,
                "structure": topic.structure,
                "visual": topic.visual,
                "time_window": topic.time_window,
                "recommendation_reason": topic.recommendation_reason,
                "credibility_label": event.credibility_label if event else None,
                "evidence": evidence_map.get(topic.hot_event_id, []),
                "feedback_status": feedback.status.value if feedback else None,
                "feedback_douyin_url": feedback.douyin_url if feedback else None,
                "plan": {
                    "core_viewpoint": plan.core_viewpoint,
                    "hooks": plan.hooks or [],
                    "structure": plan.structure,
                    "visual": plan.visual,
                    "titles": plan.titles or [],
                    "risks": plan.risks,
                } if plan else None,
            }
        )

    return [
        {
            "id": report.id,
            "user_id": report.user_id,
            "email": users[report.user_id].email,
            "report_date": report.report_date,
            "summary": report.summary,
            "reason": report.reason,
            "created_at": report.created_at,
            "mail_status": latest_delivery[report.id].status.value if report.id in latest_delivery else None,
            "topics": topics_by_report.get(report.id, []),
        }
        for report in reports
        if report.user_id in users
    ]


def _product_feedback_to_dict(row: ProductFeedback, users: dict[int, User]) -> dict:
    return {
        "id": row.id,
        "user_id": row.user_id,
        "user_email": users[row.user_id].email if row.user_id in users else None,
        "category": row.category,
        "content": row.content,
        "contact_email": row.contact_email,
        "page_url": row.page_url,
        "status": row.status,
        "created_at": row.created_at,
    }


def product_feedback_rows(db: Session, status: str | None = None) -> list[dict]:
    query = db.query(ProductFeedback).order_by(ProductFeedback.created_at.desc(), ProductFeedback.id.desc())
    if status:
        query = query.filter(ProductFeedback.status == status)
    rows = query.limit(200).all()
    user_ids = [row.user_id for row in rows if row.user_id is not None]
    users = {user.id: user for user in db.query(User).filter(User.id.in_(user_ids)).all()} if user_ids else {}
    return [_product_feedback_to_dict(row, users) for row in rows]


def product_feedback_row(db: Session, feedback_id: int) -> dict | None:
    """按 id 单条查询反馈，不受列表 200 条上限影响。"""
    row = db.get(ProductFeedback, feedback_id)
    if row is None:
        return None
    user_ids = [row.user_id] if row.user_id is not None else []
    users = {user.id: user for user in db.query(User).filter(User.id.in_(user_ids)).all()} if user_ids else {}
    return _product_feedback_to_dict(row, users)


def update_product_feedback_status(db: Session, feedback_id: int, status: str) -> ProductFeedback:
    feedback = db.get(ProductFeedback, feedback_id)
    if feedback is None:
        raise ValueError("产品反馈不存在")
    feedback.status = status
    db.commit()
    db.refresh(feedback)
    return feedback


def mail_delivery_rows(db: Session, limit: int = 200) -> list[dict]:
    rows = db.query(MailDelivery).order_by(MailDelivery.created_at.desc()).limit(limit).all()
    user_ids = {row.user_id for row in rows}
    report_ids = {row.report_id for row in rows if row.report_id is not None}
    users = {row.id: row for row in db.query(User).filter(User.id.in_(user_ids)).all()} if user_ids else {}
    reports = {
        row.id: row
        for row in db.query(PersonalizedReport).filter(PersonalizedReport.id.in_(report_ids)).all()
    } if report_ids else {}
    return [
        {
            "id": row.id,
            "user_id": row.user_id,
            "user_email": users[row.user_id].email,
            "report_id": row.report_id,
            "report_date": reports[row.report_id].report_date if row.report_id in reports else None,
            "subject": row.subject,
            "status": row.status.value,
            "error": row.error,
            "created_at": row.created_at,
            "sent_at": row.sent_at,
        }
        for row in rows
        if row.user_id in users
    ]


def subscription_rows(db: Session, limit: int = 200) -> list[dict]:
    now = utcnow()
    rows = db.query(Subscription).order_by(Subscription.created_at.desc()).limit(limit).all()
    user_ids = {row.user_id for row in rows}
    users = {row.id: row for row in db.query(User).filter(User.id.in_(user_ids)).all()} if user_ids else {}
    return [
        {
            "id": row.id,
            "user_id": row.user_id,
            "user_email": users[row.user_id].email,
            "price_type": row.price_type.value,
            "monthly_price": row.monthly_price,
            "status": row.status.value,
            "started_at": row.started_at,
            "expires_at": row.expires_at,
            "is_effective": row.status == SubscriptionStatus.active and row.expires_at > now,
        }
        for row in rows
        if row.user_id in users
    ]


def publication_feedback_rows(db: Session, limit: int = 200) -> list[dict]:
    rows = db.query(TopicFeedback).order_by(TopicFeedback.updated_at.desc()).limit(limit).all()
    user_ids = {row.user_id for row in rows}
    topic_ids = {row.topic_id for row in rows}
    users = {row.id: row for row in db.query(User).filter(User.id.in_(user_ids)).all()} if user_ids else {}
    topics = {
        row.id: row
        for row in db.query(PersonalizedTopic).filter(PersonalizedTopic.id.in_(topic_ids)).all()
    } if topic_ids else {}
    report_ids = {topic.report_id for topic in topics.values()}
    reports = {
        row.id: row
        for row in db.query(PersonalizedReport).filter(PersonalizedReport.id.in_(report_ids)).all()
    } if report_ids else {}
    result: list[dict] = []
    for row in rows:
        topic = topics.get(row.topic_id)
        report = reports.get(topic.report_id) if topic else None
        user = users.get(row.user_id)
        if not topic or not report or not user:
            continue
        result.append(
            {
                "id": row.id,
                "user_id": row.user_id,
                "user_email": user.email,
                "report_id": report.id,
                "report_date": report.report_date,
                "topic_id": topic.id,
                "topic_title": topic.title,
                "status": row.status.value,
                "douyin_url": row.douyin_url,
                "updated_at": row.updated_at,
            }
        )
    return result


def job_rows(db: Session, limit: int = 200) -> list[dict]:
    rows = db.query(Job).order_by(Job.created_at.desc()).limit(limit).all()
    return [
        {
            "id": row.id,
            "kind": row.kind.value,
            "status": row.status.value,
            "result_ref": row.result_ref,
            "error_message": row.error_message,
            "context": row.context,
            "created_at": row.created_at,
            "started_at": row.started_at,
            "finished_at": row.finished_at,
        }
        for row in rows
    ]


def _renumber(db: Session, report_id: int) -> None:
    """重新给选题编号 1..N，保持连续。"""
    topics = (
        db.query(TopicRecommendation)
        .filter(TopicRecommendation.report_id == report_id)
        .order_by(TopicRecommendation.order_index, TopicRecommendation.id)
        .all()
    )
    for i, t in enumerate(topics, start=1):
        t.order_index = i


def approve_topic(db: Session, topic_id: int) -> TopicRecommendation:
    topic = db.get(TopicRecommendation, topic_id)
    if topic is None:
        raise ValueError("选题不存在")
    topic.reviewed = True
    db.commit()
    db.refresh(topic)
    return topic


def reject_topic(db: Session, topic_id: int) -> None:
    topic = db.get(TopicRecommendation, topic_id)
    if topic is None:
        raise ValueError("选题不存在")
    report_id = topic.report_id
    db.delete(topic)
    db.flush()
    _renumber(db, report_id)
    db.commit()


def edit_topic(db: Session, topic_id: int, data: dict) -> TopicRecommendation:
    topic = db.get(TopicRecommendation, topic_id)
    if topic is None:
        raise ValueError("选题不存在")
    for key, value in data.items():
        if value is not None:
            setattr(topic, key, str(value)[:3000])
    db.commit()
    db.refresh(topic)
    return topic


def _mock_topic(event: HotEvent) -> dict:
    return {
        "title": f"[模拟选题] {event.title[:60]}",
        "what_happened": event.summary[:300],
        "why_now": "[模拟] 值得关注的理由",
        "angle": "[模拟] 通用切入角度",
        "hook": "[模拟] 前三秒钩子",
        "structure": "[模拟] 60-90 秒结构",
        "visual": "[模拟] 画面建议",
        "publish_reason": "趁热度最高",
    }


def add_topic_from_event(db: Session, event_id: int) -> TopicRecommendation:
    event = db.get(HotEvent, event_id)
    if event is None:
        raise ValueError("事件不存在")

    report = db.query(DailyReport).filter(DailyReport.report_date == _today()).first()
    if report is None:
        report = DailyReport(report_date=_today(), status=ReportStatus.draft)
        db.add(report)
        db.flush()

    event_text = (
        f"id={event.id} | 事件时间={event.first_seen_at} | 可信度={event.credibility_label.value} | "
        f"标题={event.title} | 摘要={event.summary}"
    )
    if llm.is_available():
        data = llm.complete_json(_TOPIC_PROMPT, event_text, max_tokens=3000)
    else:
        data = _mock_topic(event)

    existing_count = (
        db.query(TopicRecommendation).filter(TopicRecommendation.report_id == report.id).count()
    )
    if existing_count >= 3:
        raise ValueError("最多 3 个主选题，请先拒绝一个再补充")

    reason = str(data.get("publish_reason") or "趁热度最高").strip()
    time_window = f"建议 {_deadline_str(event.first_seen_at)} 前发布，{reason}"

    topic = TopicRecommendation(
        report_id=report.id,
        hot_event_id=event.id,
        title=str(data.get("title") or "")[:300] or event.title[:300],
        what_happened=str(data.get("what_happened") or "") or event.summary[:2000],
        why_now=str(data.get("why_now") or ""),
        angle=str(data.get("angle") or ""),
        hook=str(data.get("hook") or ""),
        structure=str(data.get("structure") or ""),
        visual=str(data.get("visual") or ""),
        time_window=time_window,
        order_index=existing_count + 1,
        reviewed=True,
    )
    db.add(topic)
    db.flush()
    _renumber(db, report.id)
    db.commit()
    db.refresh(topic)
    return topic


def publish_report(db: Session) -> DailyReport:
    report = db.query(DailyReport).filter(DailyReport.report_date == _today()).first()
    if report is None:
        raise ValueError("今日日报不存在，请先生成")
    unreviewed = (
        db.query(TopicRecommendation)
        .filter(TopicRecommendation.report_id == report.id, TopicRecommendation.reviewed.is_(False))
        .count()
    )
    if unreviewed > 0:
        raise ValueError(f"还有 {unreviewed} 个选题未质检，不能发布")
    if report.status != ReportStatus.published:
        report.status = ReportStatus.published
        report.published_at = utcnow()
        db.commit()
    return report


def candidate_events(db: Session, exclude_event_ids: set[int], limit: int = 10) -> list[HotEvent]:
    now = utcnow()
    events = (
        db.query(HotEvent)
        .filter(HotEvent.status != EventStatus.archived)
        .order_by(HotEvent.sort_score.desc())
        .limit(30)
        .all()
    )
    fresh = [e for e in events if _hours_ago(e.first_seen_at, now) <= settings.topic_fresh_relax_hours]
    return [e for e in fresh if e.id not in exclude_event_ids][:limit]
