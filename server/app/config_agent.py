"""
Phase 3 LangChain Agent 配置 —— 独立于 Phase 1 / Phase 2，避免改动一期配置。
"""

import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


class AgentSettings:
    """LangChain Agent 相关环境变量"""

    agent_max_iterations: int = int(os.getenv("AGENT_MAX_ITERATIONS", "5"))
    rate_limit_agent: str = os.getenv("RATE_LIMIT_AGENT", "10/minute")
    agent_default_system: str = os.getenv(
        "AGENT_DEFAULT_SYSTEM",
        "你是一位智能助手，可以使用 calculator 和 text_formatter 工具。"
        "遇到数学计算请调用 calculator；遇到文本格式转换请调用 text_formatter。"
        "若启用了知识库，还可使用 rag_search 检索文档后再作答。"
        "工具返回结果后，用自然语言向用户说明答案。",
    )
    agent_rag_system_suffix: str = os.getenv(
        "AGENT_RAG_SYSTEM_SUFFIX",
        "当前已绑定知识库「{kb_name}」。"
        "遇到需要依据资料回答的问题，请先调用 rag_search 检索，"
        "必要时可再调用 calculator 或 text_formatter 处理结果。",
    )


@lru_cache
def get_agent_settings() -> AgentSettings:
    return AgentSettings()
