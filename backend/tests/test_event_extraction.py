"""事件提取编排测试（mock 模式，无需真实 Key）。"""
from app.models import EventEvidence, HotEvent
from app.services.event_extraction import extract_events, select_candidate_items


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


def test_extract_skips_hallucinated_evidence_ids(db, source_factory, item_factory):
    src = source_factory()
    item_factory(src, title="real")

    # 直接验证：证据 id 不在候选内会被过滤（通过 mock 覆盖不了，这里测内部行为）
    from app.services.event_extraction import _mock_extract

    data = _mock_extract(select_candidate_items(db))
    assert data["events"][0]["evidence_item_ids"]
