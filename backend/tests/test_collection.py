"""采集编排：去重、单一源失败隔离。"""
import app.services.collection as collection_mod
from app.models import CollectionRun, Source, SourceItem
from app.models.enums import CredibilityLevel, SourceType


def _make_source(db, name="s1", type_=SourceType.rss, url="https://e.com/f"):
    s = Source(
        name=name, type=type_, url=url, enabled=True,
        credibility_level=CredibilityLevel.official, max_items_per_day=3,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def _items(urls):
    return [
        {
            "title": f"title {i}",
            "body": "body",
            "author": "a",
            "url": u,
            "published_at": None,
            "raw": {"title": f"title {i}", "link": u, "summary": "body", "published": None},
        }
        for i, u in enumerate(urls)
    ]


def test_dedup_same_url(db, monkeypatch):
    source = _make_source(db)
    monkeypatch.setattr(
        collection_mod, "fetch_items",
        lambda st, u: _items(["https://e.com/p1", "https://e.com/p2"]),
    )
    first = collection_mod.collect_source(db, source)
    assert first.items_count == 2

    # 第二次：两条重复 + 一条新
    monkeypatch.setattr(
        collection_mod, "fetch_items",
        lambda st, u: _items(["https://e.com/p1", "https://e.com/p2", "https://e.com/p3"]),
    )
    second = collection_mod.collect_source(db, source)
    assert second.items_count == 1
    assert db.query(SourceItem).count() == 3


def test_tracking_param_variants_dedup(db, monkeypatch):
    source = _make_source(db)
    monkeypatch.setattr(
        collection_mod, "fetch_items",
        lambda st, u: _items(["https://e.com/p?utm_source=x"]),
    )
    collection_mod.collect_source(db, source)
    monkeypatch.setattr(
        collection_mod, "fetch_items",
        lambda st, u: _items(["https://e.com/p"]),
    )
    result = collection_mod.collect_source(db, source)
    assert result.items_count == 0
    assert db.query(SourceItem).count() == 1


def test_single_source_failure_does_not_block(db, monkeypatch):
    s1 = _make_source(db, name="bad")
    s2 = _make_source(db, name="good", url="https://e.com/g")

    def fake_fetch(st, u):
        if st == SourceType.rss and u == "https://e.com/f":
            raise RuntimeError("boom")
        return _items(["https://e.com/g1"])

    monkeypatch.setattr(collection_mod, "fetch_items", fake_fetch)
    summary = collection_mod.collect_all(db)

    assert summary.total_sources == 2
    assert summary.success == 1
    assert summary.failed == 1
    assert summary.new_items == 1

    runs = db.query(CollectionRun).order_by(CollectionRun.id).all()
    statuses = {r.source_id: r.status.value for r in runs}
    assert statuses[s1.id] == "failed"
    assert statuses[s2.id] == "success"


def test_x_source_returns_empty(db, monkeypatch):
    source = _make_source(db, type_=SourceType.x, url="https://x.com/OpenAI")
    result = collection_mod.collect_source(db, source)
    assert result.items_count == 0
    assert db.query(SourceItem).count() == 0
