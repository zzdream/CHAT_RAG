"""聊天请求体校验测试（不调用 DeepSeek）"""

from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from app.schemas.chat import _chat_field_limits


def test_chat_stream_missing_message(client: TestClient) -> None:
    response = client.post("/chat/stream", json={})

    assert response.status_code == 422


def test_chat_stream_empty_message(client: TestClient) -> None:
    response = client.post("/chat/stream", json={"message": ""})

    assert response.status_code == 422


def test_chat_stream_sensitive_word_in_message(client: TestClient) -> None:
    response = client.post("/chat/stream", json={"message": "这里有赌博内容"})

    assert response.status_code == 422
    assert "敏感词" in response.text


def test_chat_stream_sensitive_word_in_system(client: TestClient) -> None:
    response = client.post(
        "/chat/stream",
        json={"message": "你好", "system": "讨论色情话题"},
    )

    assert response.status_code == 422
    assert "敏感词" in response.text


def test_chat_stream_sensitive_word_in_history(client: TestClient) -> None:
    response = client.post(
        "/chat/stream",
        json={
            "message": "继续",
            "history": [{"role": "user", "content": "说说暴力事件"}],
        },
    )

    assert response.status_code == 422
    assert "敏感词" in response.text


def test_chat_stream_history_exceeds_limit(client: TestClient) -> None:
    mock_settings = MagicMock(
        chat_message_max_length=4000,
        chat_system_max_length=2000,
        sensitive_words=frozenset(),
        chat_history_max_messages=2,
        chat_allowed_models=frozenset({"deepseek-v4-flash"}),
    )

    with patch("app.schemas.chat.get_settings", return_value=mock_settings):
        _chat_field_limits.cache_clear()

        response = client.post(
            "/chat/stream",
            json={
                "message": "第三条",
                "history": [
                    {"role": "user", "content": "第一条"},
                    {"role": "assistant", "content": "回复一"},
                    {"role": "user", "content": "第二条"},
                ],
            },
        )

    assert response.status_code == 422
    assert "历史消息不能超过" in response.text


def test_chat_stream_invalid_temperature(client: TestClient) -> None:
    response = client.post("/chat/stream", json={"message": "你好", "temperature": 3})

    assert response.status_code == 422


def test_chat_stream_invalid_model(client: TestClient) -> None:
    response = client.post(
        "/chat/stream",
        json={"message": "你好", "model": "unknown-model"},
    )

    assert response.status_code == 422
    assert "不支持的模型" in response.text
