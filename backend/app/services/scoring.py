"""价值排序打分（FR-04，临时方案 + 显式标注 + 可配置）。

公式（待冻结，见阶段文档风险）：
sort_score = 0.30*relevance + 0.25*actionability + 0.20*freshness + 0.25*credibility_bonus
"""
from app.models.enums import CredibilityLabel

# 权重（可配置，交付清单标注待冻结）
W_RELEVANCE = 0.30
W_ACTIONABILITY = 0.25
W_FRESHNESS = 0.20
W_CREDIBILITY = 0.25

# 可信度加成
CREDIBILITY_BONUS = {
    CredibilityLabel.official: 5.0,
    CredibilityLabel.multi_source: 3.5,
    CredibilityLabel.early_signal: 1.0,
}


def compute_sort_score(
    relevance_score: int,
    actionability_score: int,
    freshness_score: int,
    credibility_label: CredibilityLabel,
) -> float:
    bonus = CREDIBILITY_BONUS.get(credibility_label, 1.0)
    return round(
        W_RELEVANCE * relevance_score
        + W_ACTIONABILITY * actionability_score
        + W_FRESHNESS * freshness_score
        + W_CREDIBILITY * bonus,
        3,
    )
