"""创作方案生成：展开个性化选题 → 可拍摄的执行方案。"""
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import CreationPlan, CreatorProfile, PersonalizedReport, PersonalizedTopic
from . import llm

_PROMPT = (Path(__file__).resolve().parent / "prompts" / "creation_plan.md").read_text(encoding="utf-8")
_REQUIRED_TEXT_FIELDS = ("core_viewpoint", "structure", "visual", "risks")
_FORBIDDEN_MARKERS = ("[模拟]",)


class CreationPlanQualityError(ValueError):
    """创作方案未达到可交付标准。"""


def _profile_text(p: CreatorProfile) -> str:
    return (
        f"账号定位：{p.positioning}\n目标观众：{p.audience}\n人设：{p.persona}\n"
        f"表达风格：{p.style}\n视频长度：{p.video_length}\n内容禁区：{p.forbidden}"
    )


def _topic_text(t: PersonalizedTopic) -> str:
    return (
        f"标题：{t.title}\n发生了什么：{t.what_happened}\n为什么现在关注：{t.why_now}\n"
        f"切入角度：{t.angle}\n建议发布时机：{t.time_window}"
    )


def _mock(t: PersonalizedTopic) -> dict:
    return {
        "core_viewpoint": f"[模拟] 围绕「{t.title[:40]}」的核心观点",
        "hooks": ["[模拟] 开场钩子 1（接入真实 Key 后由模型生成）", "[模拟] 开场钩子 2"],
        "structure": "[模拟] 60-90 秒段落结构建议",
        "visual": "[模拟] 画面/演示建议",
        "titles": ["[模拟] 标题方向 1", "[模拟] 标题方向 2"],
        "risks": "[模拟] 风险提示：以官方信息为准，不要夸大",
    }


def _validated_data(data: dict) -> dict:
    issues: list[str] = []
    normalized = {
        field: str(data.get(field) or "").strip()
        for field in _REQUIRED_TEXT_FIELDS
    }
    hooks = [str(item).strip() for item in data.get("hooks", []) if str(item).strip()]
    titles = [str(item).strip() for item in data.get("titles", []) if str(item).strip()]

    missing = [field for field, value in normalized.items() if not value]
    if missing:
        issues.append(f"创作方案缺少字段：{', '.join(missing)}")
    if not 2 <= len(hooks) <= 3:
        issues.append(f"开场钩子必须为 2—3 个，当前为 {len(hooks)} 个")
    if not 2 <= len(titles) <= 3:
        issues.append(f"标题方向必须为 2—3 个，当前为 {len(titles)} 个")

    values = [*normalized.values(), *hooks, *titles]
    if settings.app_env == "prod" and any(
        marker in value for marker in _FORBIDDEN_MARKERS for value in values
    ):
        issues.append("创作方案包含模拟内容")
    if issues:
        raise CreationPlanQualityError("；".join(issues))

    return {**normalized, "hooks": hooks, "titles": titles}


def generate_plan(db: Session, user_id: int, topic_id: int) -> dict:
    topic = db.get(PersonalizedTopic, topic_id)
    if topic is None:
        raise ValueError("选题不存在")
    report = db.get(PersonalizedReport, topic.report_id)
    if report is None or report.user_id != user_id:
        raise ValueError("无权访问该选题")

    profile = db.query(CreatorProfile).filter(CreatorProfile.user_id == user_id).first()
    if profile is None:
        raise ValueError("请先填写创作者画像")

    existing = db.query(CreationPlan).filter(CreationPlan.topic_id == topic_id).first()
    if existing is not None:
        return {"plan_id": existing.id, "status": "already_generated"}

    user_prompt = _PROMPT.replace("{profile}", _profile_text(profile)).replace(
        "{topic}", _topic_text(topic)
    )
    if llm.is_available():
        data = llm.complete_json(_PROMPT, user_prompt, max_tokens=3000)
    else:
        if settings.app_env == "prod":
            raise CreationPlanQualityError("创作方案模型暂不可用，请稍后再试")
        data = _mock(topic)
    data = _validated_data(data)

    plan = CreationPlan(topic_id=topic_id, user_id=user_id)
    db.add(plan)
    plan.core_viewpoint = str(data.get("core_viewpoint") or "")[:2000]
    plan.hooks = [str(h)[:500] for h in data.get("hooks", [])][:3]
    plan.structure = str(data.get("structure") or "")[:3000]
    plan.visual = str(data.get("visual") or "")[:2000]
    plan.titles = [str(x)[:200] for x in data.get("titles", [])][:3]
    plan.risks = str(data.get("risks") or "")[:2000]
    db.commit()
    db.refresh(plan)
    return {"plan_id": plan.id, "status": "generated"}
