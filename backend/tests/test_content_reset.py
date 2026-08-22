"""本地内容清零只删除内容流水，保留账号、邀请码和新来源。"""
from datetime import date

from app.models import (
    CollectionRun,
    DailyReport,
    EventEvidence,
    HotBrief,
    HotEvent,
    InviteCode,
    Job,
    Source,
    SourceItem,
    User,
)
from app.models.enums import (
    CollectionStatus,
    CredibilityLabel,
    CredibilityLevel,
    EventStatus,
    JobKind,
    JobStatus,
    SourceType,
)
from app.services.content_reset import reset_local_content
from app.services.source_reconciliation import reconcile_sources
from app.services.url_normalize import url_hash


def test_reset_local_content_preserves_accounts_invites_and_desired_sources(db):
    reconcile_sources(db)
    desired_source = db.query(Source).filter_by(name="OpenAI News").one()
    legacy_source = Source(
        name="旧来源",
        type=SourceType.rss,
        url="https://legacy.example.com/feed",
        enabled=False,
        credibility_level=CredibilityLevel.media,
        max_items_per_day=3,
    )
    user = User(
        email="content-reset-check@example.com",
        password_hash="isolated-test-hash",
        is_operator=False,
    )
    db.add_all([legacy_source, user])
    db.flush()
    invite = InviteCode(code="RESET-CHECK", used=True, used_by=user.id)
    desired_item = SourceItem(
        source_id=desired_source.id,
        title="旧的官方内容",
        url="https://example.com/old-official",
        url_hash=url_hash("https://example.com/old-official"),
    )
    legacy_item = SourceItem(
        source_id=legacy_source.id,
        title="旧的聚合内容",
        url="https://example.com/old-legacy",
        url_hash=url_hash("https://example.com/old-legacy"),
    )
    db.add_all([invite, desired_item, legacy_item])
    db.flush()
    event = HotEvent(
        title="旧热点",
        summary="旧摘要",
        credibility_label=CredibilityLabel.early_signal,
        relevance_score=1,
        actionability_score=1,
        freshness_score=1,
        sort_score=1,
        status=EventStatus.candidate,
    )
    report = DailyReport(report_date=date(2026, 8, 1))
    db.add_all([event, report])
    db.flush()
    db.add_all(
        [
            EventEvidence(hot_event_id=event.id, source_item_id=legacy_item.id),
            HotBrief(report_id=report.id, hot_event_id=event.id, summary="旧速览"),
            CollectionRun(
                source_id=legacy_source.id,
                status=CollectionStatus.success,
                items_count=1,
            ),
            Job(kind=JobKind.extract_events, status=JobStatus.success),
        ]
    )
    db.commit()
    protected_snapshot = (user.id, user.email, user.password_hash, user.is_operator)

    result = reset_local_content(db)

    assert result["sources_kept"] == 13
    assert result["legacy_sources_deleted"] == 1
    assert db.query(Source).count() == 13
    assert db.query(SourceItem).count() == 0
    assert db.query(CollectionRun).count() == 0
    assert db.query(EventEvidence).count() == 0
    assert db.query(HotEvent).count() == 0
    assert db.query(HotBrief).count() == 0
    assert db.query(DailyReport).count() == 0
    assert db.query(Job).count() == 0
    preserved_user = db.query(User).filter_by(email=user.email).one()
    assert (
        preserved_user.id,
        preserved_user.email,
        preserved_user.password_hash,
        preserved_user.is_operator,
    ) == protected_snapshot
    assert db.query(InviteCode).filter_by(code="RESET-CHECK").one().used_by == user.id
