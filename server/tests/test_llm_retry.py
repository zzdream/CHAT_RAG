"""LLM 重试工具测试"""

from unittest.mock import MagicMock, patch

import pytest
from openai import APIError

from app.services.llm_retry import (
    chat_completion_create_with_retry,
    is_retryable_api_error,
)


def test_is_retryable_api_error() -> None:
    exc429 = APIError("rate limit", request=MagicMock(), body=None)
    exc429.status_code = 429
    assert is_retryable_api_error(exc429)

    exc503 = APIError("server error", request=MagicMock(), body=None)
    exc503.status_code = 503
    assert is_retryable_api_error(exc503)

    exc401 = APIError("unauthorized", request=MagicMock(), body=None)
    exc401.status_code = 401
    assert not is_retryable_api_error(exc401)


@patch("app.services.llm_retry.get_retry_settings")
def test_chat_completion_create_with_retry_success(mock_settings) -> None:
    mock_settings.return_value.llm_retry_enabled = True
    mock_settings.return_value.llm_retry_max_attempts = 3
    mock_settings.return_value.llm_retry_min_wait = 0.01
    mock_settings.return_value.llm_retry_max_wait = 0.02

    client = MagicMock()
    client.chat.completions.create.return_value = {"ok": True}

    result = chat_completion_create_with_retry(client, model="test", messages=[])

    assert result == {"ok": True}
    assert client.chat.completions.create.call_count == 1


@patch("app.services.llm_retry.get_retry_settings")
def test_chat_completion_create_with_retry_on_429(mock_settings) -> None:
    mock_settings.return_value.llm_retry_enabled = True
    mock_settings.return_value.llm_retry_max_attempts = 3
    mock_settings.return_value.llm_retry_min_wait = 0.01
    mock_settings.return_value.llm_retry_max_wait = 0.02

    client = MagicMock()
    exc429 = APIError("rate limit", request=MagicMock(), body=None)
    exc429.status_code = 429
    client.chat.completions.create.side_effect = [exc429, {"ok": True}]

    retries: list[int] = []

    result = chat_completion_create_with_retry(
        client,
        on_retry=lambda attempt, _max, _exc: retries.append(attempt),
        model="test",
        messages=[],
    )

    assert result == {"ok": True}
    assert client.chat.completions.create.call_count == 2
    assert retries == [1]
