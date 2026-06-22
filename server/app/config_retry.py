"""
Phase 3 LLM 重试配置 —— 独立于 Phase 1 config.py。
"""

import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


class RetrySettings:
    """LLM API 重试相关环境变量（Phase 3 Agent / Tools 使用）"""

    llm_retry_enabled: bool = os.getenv("LLM_RETRY_ENABLED", "true").lower() == "true"
    llm_retry_max_attempts: int = int(os.getenv("LLM_RETRY_MAX_ATTEMPTS", "3"))
    llm_retry_min_wait: float = float(os.getenv("LLM_RETRY_MIN_WAIT", "1"))
    llm_retry_max_wait: float = float(os.getenv("LLM_RETRY_MAX_WAIT", "8"))


@lru_cache
def get_retry_settings() -> RetrySettings:
    return RetrySettings()
