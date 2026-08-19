"""可信度标签确定性计算（FR-05）。

规则：
- 证据含 ≥1 个官方信息源 → official（官方确认）
- 否则证据来自 ≥2 个**不同**信息源 → multi_source（多方报道）
- 否则（单一非官方来源）→ early_signal（早期信号）

输入 evidence_sources：每个元素是 (source_id, credibility_level) 元组，
source_id 用于判断"独立来源"，credibility_level 用于判断"是否官方"。
"""
from collections.abc import Iterable

from app.models.enums import CredibilityLevel, CredibilityLabel


def compute_credibility(
    evidence_sources: Iterable[tuple[object, str | CredibilityLevel]],
) -> CredibilityLabel:
    sources = list(evidence_sources)
    if not sources:
        return CredibilityLabel.early_signal

    if any(level in (CredibilityLevel.official, "official") for _, level in sources):
        return CredibilityLabel.official

    distinct_sources = len({source_id for source_id, _ in sources})
    if distinct_sources >= 2:
        return CredibilityLabel.multi_source

    return CredibilityLabel.early_signal
