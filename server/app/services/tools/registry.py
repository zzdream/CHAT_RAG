"""
工具注册表 —— OpenAI Function Calling schema 定义与统一调度。
"""

import json
from typing import Any

from app.services.tools.calculator import calculate
from app.services.tools.text_formatter import format_text

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": (
                "计算数学表达式。支持加减乘除、整除、取模、幂运算与括号。"
                "示例：'123 * 456'、'(1 + 2) * 3'。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "要计算的数学表达式",
                    }
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "text_formatter",
            "description": (
                "格式化文本。format_type 可选："
                "uppercase（大写）、lowercase（小写）、title（标题大小写）、"
                "trim（去首尾空格）、reverse（反转）、json_pretty（JSON 美化）。"
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "待格式化的文本",
                    },
                    "format_type": {
                        "type": "string",
                        "description": "格式类型",
                        "enum": [
                            "uppercase",
                            "lowercase",
                            "title",
                            "trim",
                            "reverse",
                            "json_pretty",
                        ],
                    },
                },
                "required": ["text", "format_type"],
            },
        },
    },
]


def execute_tool(name: str, arguments: str) -> str:
    """解析 JSON 参数并执行对应工具，返回字符串结果。"""
    try:
        args = json.loads(arguments) if arguments else {}
    except json.JSONDecodeError as exc:
        raise ValueError(f"工具参数不是合法 JSON: {exc.msg}") from exc

    if not isinstance(args, dict):
        raise ValueError("工具参数必须是 JSON 对象")

    if name == "calculator":
        expression = args.get("expression")
        if not isinstance(expression, str) or not expression.strip():
            raise ValueError("calculator 需要非空 expression 参数")
        return calculate(expression)

    if name == "text_formatter":
        text = args.get("text")
        format_type = args.get("format_type")
        if not isinstance(text, str):
            raise ValueError("text_formatter 需要 text 参数")
        if not isinstance(format_type, str) or not format_type.strip():
            raise ValueError("text_formatter 需要 format_type 参数")
        return format_text(text, format_type)

    raise ValueError(f"未知工具: {name}")
