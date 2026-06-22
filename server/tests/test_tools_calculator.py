"""calculator 工具单元测试"""

import pytest

from app.services.tools.calculator import calculate


def test_calculate_basic() -> None:
    assert calculate("1 + 2") == "3"
    assert calculate("123 * 456") == "56088"


def test_calculate_parentheses_and_power() -> None:
    assert calculate("(1 + 2) * 3") == "9"
    assert calculate("2 ** 10") == "1024"


def test_calculate_division() -> None:
    assert calculate("10 / 4") == "2.5"
    assert calculate("10 // 4") == "2"


def test_calculate_empty_expression() -> None:
    with pytest.raises(ValueError, match="表达式不能为空"):
        calculate("   ")


def test_calculate_invalid_syntax() -> None:
    with pytest.raises(ValueError, match="语法错误"):
        calculate("1 + * 2")


def test_calculate_division_by_zero() -> None:
    with pytest.raises(ValueError, match="除数不能为零"):
        calculate("1 / 0")


def test_calculate_unsupported_node() -> None:
    with pytest.raises(ValueError, match="不支持的"):
        calculate("__import__('os')")
