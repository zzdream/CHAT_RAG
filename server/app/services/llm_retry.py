"""
LLM API 重试工具 —— Phase 3 专用，不修改 Phase 1 的 llm.py。

对 429 / 5xx 等 transient 错误做指数退避重试。
"""

from collections.abc import Callable
from typing import Any, TypeVar

from openai import APIError, OpenAI
from tenacity import (
    Retrying,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from app.config_retry import RetrySettings, get_retry_settings

T = TypeVar("T")

RETRYABLE_STATUS_CODES = frozenset({408, 429, 500, 502, 503, 504})


def is_retryable_api_error(exc: BaseException) -> bool:
    """判断 OpenAI SDK 异常是否值得重试。"""
    if isinstance(exc, APIError):
        status_code = getattr(exc, "status_code", None)
        return status_code in RETRYABLE_STATUS_CODES
    return False


def build_retrying(
    settings: RetrySettings | None = None,
    *,
    on_retry: Callable[[int, int, BaseException], None] | None = None,
) -> Retrying:
    """创建 tenacity Retrying 实例。"""
    config = settings or get_retry_settings()
    max_attempts = config.llm_retry_max_attempts if config.llm_retry_enabled else 1

    def _before_sleep(retry_state: Any) -> None:
        if on_retry is None:
            return
        exc = retry_state.outcome.exception() if retry_state.outcome else None
        if exc is not None:
            on_retry(retry_state.attempt_number, max_attempts, exc)

    return Retrying(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(
            multiplier=config.llm_retry_min_wait,
            max=config.llm_retry_max_wait,
        ),
        retry=retry_if_exception(is_retryable_api_error),
        before_sleep=_before_sleep,
        reraise=True,
    )


def chat_completion_create_with_retry(
    client: OpenAI,
    *,
    on_retry: Callable[[int, int, BaseException], None] | None = None,
    settings: RetrySettings | None = None,
    **kwargs: Any,
) -> Any:
    """带重试的 chat.completions.create 封装。"""
    config = settings or get_retry_settings()
    if not config.llm_retry_enabled:
        return client.chat.completions.create(**kwargs)

    retryer = build_retrying(config, on_retry=on_retry)
    for attempt in retryer:
        with attempt:
            return client.chat.completions.create(**kwargs)

    raise RuntimeError("chat_completion_create_with_retry 未返回结果")


def get_chat_openai_max_retries(settings: RetrySettings | None = None) -> int:
    """LangChain ChatOpenAI 使用的 max_retries 参数。"""
    config = settings or get_retry_settings()
    if not config.llm_retry_enabled:
        return 0
    return max(config.llm_retry_max_attempts - 1, 0)
