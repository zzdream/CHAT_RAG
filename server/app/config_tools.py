"""
Phase 3 工具调用配置 —— 独立于 Phase 1 的 config.py，避免改动一期配置。
"""

import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


class ToolsSettings:
    """Function Calling / 自定义工具相关环境变量"""

    tools_max_iterations: int = int(os.getenv("TOOLS_MAX_ITERATIONS", "5"))
    rate_limit_tools: str = os.getenv("RATE_LIMIT_TOOLS", "10/minute")
    tools_default_system: str = os.getenv(
        "TOOLS_DEFAULT_SYSTEM",
        "你是一位智能助手，可以使用 calculator 和 text_formatter 工具。"
        "遇到数学计算请调用 calculator；遇到文本格式转换请调用 text_formatter。"
        "工具返回结果后，用自然语言向用户说明答案。",
    )


@lru_cache
def get_tools_settings() -> ToolsSettings:
    return ToolsSettings()
