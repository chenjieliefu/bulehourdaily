"""排序打分测试（FR-04）。"""
from app.models.enums import CredibilityLabel
from app.services.scoring import compute_sort_score


def test_official_scores_higher_than_early_signal():
    official = compute_sort_score(4, 4, 4, CredibilityLabel.official)
    early = compute_sort_score(4, 4, 4, CredibilityLabel.early_signal)
    assert official > early


def test_higher_relevance_scores_higher():
    low = compute_sort_score(1, 4, 4, CredibilityLabel.official)
    high = compute_sort_score(5, 4, 4, CredibilityLabel.official)
    assert high > low
