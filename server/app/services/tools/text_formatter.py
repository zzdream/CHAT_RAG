"""
文本格式化工具 —— 大小写转换、trim、反转、JSON 美化等。
"""

import json

SUPPORTED_FORMATS = frozenset(
    {"uppercase", "lowercase", "title", "trim", "reverse", "json_pretty"}
)


def format_text(text: str, format_type: str) -> str:
    """
    按指定类型格式化文本。

    format_type 可选：uppercase, lowercase, title, trim, reverse, json_pretty
    """
    fmt = format_type.strip().lower()
    if fmt not in SUPPORTED_FORMATS:
        allowed = "、".join(sorted(SUPPORTED_FORMATS))
        raise ValueError(f"不支持的格式类型: {format_type}，可选：{allowed}")

    if fmt == "uppercase":
        return text.upper()
    if fmt == "lowercase":
        return text.lower()
    if fmt == "title":
        return text.title()
    if fmt == "trim":
        return text.strip()
    if fmt == "reverse":
        return text[::-1]
    if fmt == "json_pretty":
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"JSON 解析失败: {exc.msg}") from exc
        return json.dumps(parsed, ensure_ascii=False, indent=2)

    raise ValueError(f"不支持的格式类型: {format_type}")
