"""运营工作台聚合数据测试。"""
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.core.time import utcnow
from app.models import (
    CreationPlan,
    CreatorProfile,
    DailyReport,
    HotEvent,
    Job,
    MailDelivery,
    PersonalizedReport,
    PersonalizedTopic,
    ProductFeedback,
    Subscription,
    TopicFeedback,
    TopicRecommendation,
    User,
)
from app.models.enums import (
    CredibilityLabel,
    FeedbackStatus,
    MailStatus,
    JobKind,
    JobStatus,
    PriceType,
    ReportStatus,
    SubscriptionStatus,
)
from app.services import admin as admin_svc
from app.services import site_content as site_content_svc


def _user(db, email: str, *, operator: bool = False) -> User:
    user = User(email=email, password_hash="test", is_operator=operator)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _profile(db, user: User) -> CreatorProfile:
    profile = CreatorProfile(
        user_id=user.id,
        positioning="AI 工具测评",
        audience="AI 新手",
        persona="邻家老师",
        style="口语化",
        video_length="60 秒",
        forbidden="无",
    )
    db.add(profile)
    db.commit()
    return profile


def _personalized_report(db, user: User, report_date) -> PersonalizedReport:
    report = PersonalizedReport(
        user_id=user.id,
        report_date=report_date,
        summary="今天适合你的选题",
        reason="符合你的 AI 工具测评定位",
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def test_operations_overview_excludes_operator_and_counts_actionable_state(db):
    today = datetime.now(ZoneInfo("Asia/Shanghai")).date()
    _user(db, "operator@example.com", operator=True)
    trial = _user(db, "trial@example.com")
    subscriber = _user(db, "subscriber@example.com")
    _profile(db, trial)
    _profile(db, subscriber)
    _personalized_report(db, trial, today)
    _personalized_report(db, subscriber, today)
    db.add(
        Subscription(
            user_id=subscriber.id,
            price_type=PriceType.founding,
            monthly_price=29,
            status=SubscriptionStatus.active,
            started_at=utcnow(),
            expires_at=utcnow() + timedelta(days=3),
        )
    )
    public_report = DailyReport(report_date=today, status=ReportStatus.draft)
    event = HotEvent(title="事件", summary="摘要", credibility_label=CredibilityLabel.official)
    db.add_all([public_report, event])
    db.flush()
    db.add(
        TopicRecommendation(
            report_id=public_report.id,
            hot_event_id=event.id,
            title="选题",
            what_happened="发生了什么",
            why_now="为什么",
            angle="角度",
            hook="钩子",
            structure="结构",
            visual="画面",
            time_window="今天",
            order_index=1,
            reviewed=False,
        )
    )
    db.add(ProductFeedback(user_id=trial.id, category="content", content="这条内容不够准确"))
    db.commit()

    result = admin_svc.operations_overview(db)

    assert result["creators_total"] == 2
    assert result["profiles_completed"] == 2
    assert result["active_subscribers"] == 1
    assert result["trial_creators"] == 1
    assert result["expiring_subscribers"] == 1
    assert result["today_personalized_reports"] == 2
    assert result["today_personalized_expected"] == 2
    assert result["unreviewed_topics"] == 1
    assert result["new_product_feedback"] == 1


def test_creator_rows_and_personalized_content_include_quality_signals(db):
    today = datetime.now(ZoneInfo("Asia/Shanghai")).date()
    creator = _user(db, "creator@example.com")
    _profile(db, creator)
    report = _personalized_report(db, creator, today)
    event = HotEvent(title="新模型发布", summary="模型更新", credibility_label=CredibilityLabel.official)
    db.add(event)
    db.flush()
    topic = PersonalizedTopic(
        report_id=report.id,
        hot_event_id=event.id,
        title="新模型值不值得用",
        what_happened="发布了新模型",
        why_now="今天刚发布",
        angle="从普通用户体验切入",
        hook="这个模型可能省你一半时间",
        structure="演示、比较、结论",
        visual="录屏",
        time_window="今天发布",
        recommendation_reason="符合 AI 工具测评定位",
        order_index=1,
    )
    db.add(topic)
    db.flush()
    db.add_all(
        [
            CreationPlan(
                topic_id=topic.id,
                user_id=creator.id,
                core_viewpoint="效率提升明显",
                hooks=["先看结果"],
                structure="前后对比",
                visual="产品录屏",
                titles=["实测新模型"],
                risks="不要夸大",
            ),
            TopicFeedback(user_id=creator.id, topic_id=topic.id, status=FeedbackStatus.published),
            MailDelivery(
                user_id=creator.id,
                report_id=report.id,
                subject="日报",
                body="内容",
                status=MailStatus.sent,
                sent_at=utcnow(),
            ),
        ]
    )
    db.commit()

    creators = admin_svc.creator_operations_rows(db)
    content = admin_svc.personalized_content_rows(db, user_id=creator.id)

    assert creators[0]["entitlement_status"] == "trial"
    assert creators[0]["personalized_report_count"] == 1
    assert creators[0]["creation_plan_count"] == 1
    assert creators[0]["feedback_published"] == 1
    assert creators[0]["latest_mail_status"] == "sent"
    assert creators[0]["latest_interaction_at"] is not None
    assert content[0]["email"] == "creator@example.com"
    assert content[0]["mail_status"] == "sent"
    assert content[0]["topics"][0]["feedback_status"] == "published"
    assert content[0]["topics"][0]["plan"]["core_viewpoint"] == "效率提升明显"


def test_product_feedback_can_be_filtered_and_advanced(db):
    creator = _user(db, "feedback@example.com")
    row = ProductFeedback(user_id=creator.id, category="bug", content="页面上的按钮没有反应")
    db.add(row)
    db.commit()
    db.refresh(row)

    admin_svc.update_product_feedback_status(db, row.id, "in_progress")
    result = admin_svc.product_feedback_rows(db, status="in_progress")

    assert len(result) == 1
    assert result[0]["user_email"] == creator.email
    assert result[0]["status"] == "in_progress"


def test_delivery_subscription_feedback_and_job_rows(db):
    today = datetime.now(ZoneInfo("Asia/Shanghai")).date()
    creator = _user(db, "operations@example.com")
    report = _personalized_report(db, creator, today)
    event = HotEvent(title="发布事件", summary="摘要", credibility_label=CredibilityLabel.official)
    db.add(event)
    db.flush()
    topic = PersonalizedTopic(
        report_id=report.id, hot_event_id=event.id, title="准备发布的选题",
        what_happened="发生", why_now="现在", angle="角度", hook="钩子",
        structure="结构", visual="画面", time_window="今天",
        recommendation_reason="匹配", order_index=1,
    )
    db.add(topic)
    db.flush()
    db.add_all([
        MailDelivery(user_id=creator.id, report_id=report.id, subject="今日个性化日报", body="内容", status=MailStatus.failed, error="模拟失败"),
        Subscription(user_id=creator.id, price_type=PriceType.standard, monthly_price=49, status=SubscriptionStatus.active, started_at=utcnow(), expires_at=utcnow() + timedelta(days=30)),
        TopicFeedback(user_id=creator.id, topic_id=topic.id, status=FeedbackStatus.want),
        Job(kind=JobKind.personalized_report, status=JobStatus.failed, context={"user_id": creator.id}, error_message="生成失败"),
    ])
    db.commit()

    assert admin_svc.mail_delivery_rows(db)[0]["report_date"] == today
    assert admin_svc.subscription_rows(db)[0]["is_effective"] is True
    assert admin_svc.publication_feedback_rows(db)[0]["topic_title"] == "准备发布的选题"
    assert admin_svc.job_rows(db)[0]["context"] == {"user_id": creator.id}


def test_site_content_supports_draft_publish_and_rollback(db):
    initial = site_content_svc.get_or_create(db, "product_intro")
    old_title = initial.published["title"]
    edited = {**initial.draft, "title": "新的产品标题"}

    site_content_svc.save_draft(db, "product_intro", edited)
    assert site_content_svc.get_or_create(db, "product_intro").published["title"] == old_title
    site_content_svc.publish(db, "product_intro")
    assert site_content_svc.get_or_create(db, "product_intro").published["title"] == "新的产品标题"
    site_content_svc.rollback(db, "product_intro")
    assert site_content_svc.get_or_create(db, "product_intro").published["title"] == old_title


def test_product_feedback_row_finds_old_feedback_beyond_list_limit(db):
    first = ProductFeedback(category="other", content="第一条反馈")
    db.add(first)
    db.flush()
    for _ in range(204):
        db.add(ProductFeedback(category="other", content="后续反馈"))
    db.commit()
    db.refresh(first)

    assert len(admin_svc.product_feedback_rows(db)) == 200
    row = admin_svc.product_feedback_row(db, first.id)
    assert row is not None
    assert row["id"] == first.id
