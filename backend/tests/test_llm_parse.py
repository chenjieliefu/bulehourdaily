"""LLM 结构化输出容错解析测试。"""
import pytest

from app.services.llm import LLMError, _parse_json


def test_parse_plain_json():
    assert _parse_json('{"a": 1}') == {"a": 1}


def test_parse_markdown_fence():
    assert _parse_json('```json\n{"a": 1}\n```') == {"a": 1}


def test_parse_with_surrounding_text():
    assert _parse_json('解释文字 {"a": 1} 结尾') == {"a": 1}


def test_parse_nested_json():
    assert _parse_json('{"events": [{"id": 1, "nested": {"x": 2}}]}') == {
        "events": [{"id": 1, "nested": {"x": 2}}]
    }


def test_parse_invalid_raises():
    with pytest.raises(LLMError):
        _parse_json("这不是 JSON")


def test_parse_non_object_raises():
    with pytest.raises(LLMError):
        _parse_json("[1, 2, 3]")
