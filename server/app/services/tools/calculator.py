"""
安全计算器 —— 仅支持数字与基本算术运算符，不使用 eval()。
"""

import ast
import operator
from typing import Any

_BIN_OPS: dict[type, Any] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_UNARY_OPS: dict[type, Any] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _eval_node(node: ast.AST) -> int | float:
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)

    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"不支持的常量类型: {type(node.value).__name__}")

    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _BIN_OPS:
            raise ValueError(f"不支持的运算符: {op_type.__name__}")
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        return _BIN_OPS[op_type](left, right)

    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _UNARY_OPS:
            raise ValueError(f"不支持的一元运算符: {op_type.__name__}")
        return _UNARY_OPS[op_type](_eval_node(node.operand))

    raise ValueError(f"不支持的表达式节点: {type(node).__name__}")


def calculate(expression: str) -> str:
    """
    计算数学表达式并返回字符串结果。

    支持：+ - * / // % ** 括号、整数与小数。
    """
    expr = expression.strip()
    if not expr:
        raise ValueError("表达式不能为空")

    if len(expr) > 200:
        raise ValueError("表达式过长，最多 200 个字符")

    try:
        tree = ast.parse(expr, mode="eval")
        result = _eval_node(tree)
    except SyntaxError as exc:
        raise ValueError(f"表达式语法错误: {exc.msg}") from exc
    except ZeroDivisionError as exc:
        raise ValueError("除数不能为零") from exc

    if isinstance(result, float) and result.is_integer():
        return str(int(result))
    return str(result)
