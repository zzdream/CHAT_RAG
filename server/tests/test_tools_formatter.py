"""text_formatter 工具单元测试"""

import pytest

from app.services.tools.text_formatter import format_text


def test_format_uppercase() -> None:
    assert format_text("hello world", "uppercase") == "HELLO WORLD"


def test_format_lowercase() -> None:
    assert format_text("Hello World", "lowercase") == "hello world"


def test_format_title() -> None:
    assert format_text("hello world", "title") == "Hello World"


def test_format_trim() -> None:
    assert format_text("  hello  ", "trim") == "hello"


def test_format_reverse() -> None:
    assert format_text("abc", "reverse") == "cba"


def test_format_json_pretty() -> None:
    result = format_text('{"a":1,"b":2}', "json_pretty")
    assert '"a": 1' in result
    assert '"b": 2' in result


def test_format_invalid_type() -> None:
    with pytest.raises(ValueError, match="不支持的格式类型"):
        format_text("hello", "unknown")


def test_format_invalid_json() -> None:
    with pytest.raises(ValueError, match="JSON 解析失败"):
        format_text("{invalid", "json_pretty")
