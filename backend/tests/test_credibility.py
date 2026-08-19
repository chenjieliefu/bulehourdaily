"""可信度确定性计算测试（FR-05）。"""
from app.models.enums import CredibilityLabel
from app.services.credibility import compute_credibility


def test_official_wins_over_media():
    assert compute_credibility([("a", "official"), ("b", "media")]) == CredibilityLabel.official


def test_two_different_media_sources_is_multi_source():
    assert (
        compute_credibility([("a", "media"), ("b", "media")])
        == CredibilityLabel.multi_source
    )


def test_two_items_from_same_media_source_is_early_signal():
    assert (
        compute_credibility([("a", "media"), ("a", "media")])
        == CredibilityLabel.early_signal
    )


def test_single_non_official_is_early_signal():
    assert compute_credibility([("a", "media")]) == CredibilityLabel.early_signal


def test_empty_is_early_signal():
    assert compute_credibility([]) == CredibilityLabel.early_signal
