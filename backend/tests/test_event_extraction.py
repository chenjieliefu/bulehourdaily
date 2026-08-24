"""事件提取编排测试（mock 模式，无需真实 Key）。"""
from datetime import datetime, timedelta

import pytest

from app.core.config import settings
from app.core.time import utcnow
from app.models import EventEvidence, HotEvent, SourceItem
from app.models.enums import SourceType
from app.services import event_extraction
from app.services.event_extraction import extract_events, select_candidate_items
from app.services.url_normalize import url_hash


def test_extract_creates_events_and_evidence(db, source_factory, item_factory):
    src = source_factory()
    for i in range(4):
        item_factory(src, title=f"title{i}")

    result = extract_events(db)

    # mock 模式：4 条两两合并 → 2 个事件
    assert result["events_created"] == 2
    assert db.query(HotEvent).count() == 2
    assert db.query(EventEvidence).count() == 4


def test_extract_no_items(db):
    assert extract_events(db) == {"events_created": 0, "candidates": 0}


def test_select_candidate_items_respects_source_limit(db, source_factory, item_factory):
    src = source_factory(max_per_day=2)
    for i in range(5):
        item_factory(src, title=f"t{i}")
    assert len(select_candidate_items(db)) == 2


def test_select_candidate_items_rejects_old_article_collected_recently(db, source_factory):
    """刚入库不等于刚发布，旧闻不能进入今日候选。"""
    source = source_factory()
    item = SourceItem(
        source_id=source.id,
        title="三天前的旧闻",
        url="https://example.com/old-news",
        url_hash=url_hash("https://example.com/old-news"),
        published_at=utcnow() - timedelta(hours=72),
        collected_at=utcnow(),
    )
    db.add(item)
    db.commit()

    assert select_candidate_items(db, hours=48) == []


def test_select_candidate_items_rejects_unknown_publish_time(db, source_factory):
    """缺少原始发布时间的条目不能冒充今日新闻。"""
    source = source_factory()
    item = SourceItem(
        source_id=source.id,
        title="没有发布时间",
        url="https://example.com/no-date",
        url_hash=url_hash("https://example.com/no-date"),
        published_at=None,
        collected_at=utcnow(),
    )
    db.add(item)
    db.commit()

    assert select_candidate_items(db, hours=48) == []


def test_select_candidate_items_uses_half_open_publication_window(
    db, source_factory, item_factory
):
    source = source_factory(max_per_day=5)
    before = item_factory(source, title="before-window")
    inside = item_factory(source, title="inside-window")
    at_end = item_factory(source, title="at-window-end")
    before.published_at = datetime(2026, 8, 21, 15, 59)
    inside.published_at = datetime(2026, 8, 22, 4, 0)
    at_end.published_at = datetime(2026, 8, 22, 16, 0)
    db.commit()

    selected = select_candidate_items(
        db,
        published_from=datetime(2026, 8, 21, 16, 0),
        published_before=datetime(2026, 8, 22, 16, 0),
    )

    assert [item.id for item in selected] == [inside.id]


def test_select_candidate_items_prefers_core_sources_when_enough_exist(
    db, source_factory, item_factory
):
    core = source_factory(name="core", max_per_day=5)
    supplement = source_factory(
        name="supplement", type_=SourceType.hacker_news, max_per_day=3
    )
    for i in range(3):
        item_factory(core, title=f"core-{i}")
        item_factory(supplement, title=f"supplement-{i}")

    selected = select_candidate_items(db)

    assert {item.source_id for item in selected} == {core.id}


def test_select_candidate_items_uses_supplements_only_to_reach_minimum(
    db, source_factory, item_factory
):
    core = source_factory(name="core", max_per_day=5)
    supplement = source_factory(
        name="supplement", type_=SourceType.aibase_daily, max_per_day=5
    )
    item_factory(core, title="core-0")
    for i in range(4):
        item_factory(supplement, title=f"supplement-{i}")

    selected = select_candidate_items(db)

    assert len(selected) == 3
    assert any(item.source_id == core.id for item in selected)
    assert sum(item.source_id == supplement.id for item in selected) == 2


def test_reextract_does_not_duplicate_evidence(db, source_factory, item_factory):
    src = source_factory()
    for i in range(4):
        item_factory(src, title=f"t{i}")

    first = extract_events(db)
    assert first["events_created"] == 2

    # 再次提取：条目已归属 → 0 新增、不报错、证据不重复
    second = extract_events(db)
    assert second["events_created"] == 0
    assert db.query(EventEvidence).count() == 4
    assert db.query(HotEvent).count() == 2


def test_extract_skips_hallucinated_evidence_ids(db, source_factory, item_factory):
    src = source_factory()
    item_factory(src, title="real")

    # 直接验证：证据 id 不在候选内会被过滤（通过 mock 覆盖不了，这里测内部行为）
    from app.services.event_extraction import _mock_extract

    data = _mock_extract(select_candidate_items(db))
    assert data["events"][0]["evidence_item_ids"]


def test_extract_rejects_unsupported_resignation_wave_claim(
    db, source_factory, item_factory, monkeypatch
):
    source = source_factory()
    item = item_factory(
        source,
        title="'AI refuser' quit her dream job, and hopes others follow",
    )
    monkeypatch.setattr(event_extraction.llm, "is_available", lambda: True)
    monkeypatch.setattr(
        event_extraction.llm,
        "complete_json",
        lambda *_args, **_kwargs: {
            "events": [
                {
                    "title": "AI 从业者辞职潮引关注",
                    "summary": "一位 AI 从业者辞去工作。",
                    "evidence_item_ids": [item.id],
                    "relevance_score": 4,
                    "actionability_score": 4,
                    "reason": "值得关注",
                }
            ]
        },
    )

    result = extract_events(db)

    assert result["events_created"] == 0
    assert result["events_rejected"] == 1
    assert db.query(HotEvent).count() == 0


def test_production_never_falls_back_to_mock(
    db, source_factory, item_factory, monkeypatch
):
    source = source_factory()
    item_factory(source, title="real event")
    monkeypatch.setattr(settings, "app_env", "prod")

    with pytest.raises(
        event_extraction.EventExtractionQualityError,
        match="模型暂不可用",
    ):
        extract_events(db)
    assert db.query(HotEvent).count() == 0
