"""LLM 客户端：OpenAI 兼容接口 + 容错 JSON 解析 + 有限重试。

- 无 Key 时 is_available() 为 False，编排层切 mock。
- 密钥只在后端读取，不回显、不进日志。
"""
import json
import re

import httpx

from app.core.config import settings


class LLMError(Exception):
    """模型调用失败（网络/无 Key/解析失败）。"""


def is_available() -> bool:
    return bool(settings.model_api_key)


def _parse_json(text: str) -> dict:
    """容错解析：去掉 markdown 代码块，取第一个 { 到最后一个 }。"""
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise LLMError("模型输出不是 JSON")
    try:
        data = json.loads(text[start : end + 1])
    except json.JSONDecodeError as exc:
        raise LLMError(f"模型输出 JSON 解析失败: {exc}") from exc
    if not isinstance(data, dict):
        raise LLMError("模型输出 JSON 顶层不是对象")
    return data


def complete_json(system_prompt: str, user_prompt: str, max_tokens: int = 6000) -> dict:
    """调用模型并返回解析后的 JSON 对象。失败重试有限次数。"""
    if not is_available():
        raise LLMError("未配置 MODEL_API_KEY")

    last_err: Exception | None = None
    for attempt in range(settings.model_max_retries + 1):
        try:
            resp = httpx.post(
                f"{settings.model_base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {settings.model_api_key}"},
                json={
                    "model": settings.model_name,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "temperature": 0.4,
                    "max_tokens": max_tokens,
                    "response_format": {"type": "json_object"},
                },
                timeout=settings.model_timeout_seconds,
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            return _parse_json(content)
        except (httpx.HTTPError, LLMError, KeyError, IndexError) as exc:
            last_err = exc
            if attempt < settings.model_max_retries:
                continue
    raise LLMError(f"模型调用失败（重试 {settings.model_max_retries} 次）: {last_err}")
