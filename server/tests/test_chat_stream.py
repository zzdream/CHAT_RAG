"""流式聊天接口测试 —— mock DeepSeek，验证 SSE 与 messages 拼接"""

import json
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.services.llm import LLMServiceError


def parse_sse_events(text: str) -> list[dict]:
    events: list[dict] = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("data: "):
            events.append(json.loads(line[6:]))
    return events


def test_chat_stream_without_api_key(client: TestClient) -> None:
    with patch("app.api.routes.chat.get_settings") as mock_get_settings:
        mock_get_settings.return_value.deepseek_api_key = ""

        response = client.post("/chat/stream", json={"message": "你好"})

    assert response.status_code == 500
    assert "DEEPSEEK_API_KEY" in response.json()["detail"]


@patch("app.api.routes.chat.chat_completion_stream")
def test_chat_stream_success_sse(mock_stream, client: TestClient) -> None:
    mock_stream.return_value = iter(["你", "好"])

    response = client.post("/chat/stream", json={"message": "你好", "temperature": 0.5})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

    events = parse_sse_events(response.text)
    assert events[0] == {"content": "你"}
    assert events[1] == {"content": "好"}
    assert events[-1] == {"done": True}

    mock_stream.assert_called_once()
    messages = mock_stream.call_args[0][0]
    assert messages == [{"role": "user", "content": "你好"}]
    assert mock_stream.call_args.kwargs["temperature"] == 0.5


@patch("app.api.routes.chat.chat_completion_stream")
def test_chat_stream_includes_usage(mock_stream, client: TestClient) -> None:
    def fake_stream(*_args, **kwargs):
        usage_out = kwargs.get("usage_out")
        if usage_out is not None:
            usage_out.append(
                {
                    "prompt_tokens": 12,
                    "completion_tokens": 8,
                    "total_tokens": 20,
                }
            )
        return iter(["好"])

    mock_stream.side_effect = fake_stream

    response = client.post("/chat/stream", json={"message": "你好"})

    assert response.status_code == 200
    events = parse_sse_events(response.text)
    assert events[0] == {"content": "好"}
    assert events[1] == {
        "usage": {
            "prompt_tokens": 12,
            "completion_tokens": 8,
            "total_tokens": 20,
        }
    }
    assert events[-1] == {"done": True}


@patch("app.api.routes.chat.chat_completion_stream")
def test_chat_stream_with_system_and_history(mock_stream, client: TestClient) -> None:
    mock_stream.return_value = iter(["小明"])

    response = client.post(
        "/chat/stream",
        json={
            "message": "我叫什么？",
            "system": "你是助手",
            "history": [
                {"role": "user", "content": "我叫小明"},
                {"role": "assistant", "content": "你好小明！"},
            ],
        },
    )

    assert response.status_code == 200
    events = parse_sse_events(response.text)
    assert events[0] == {"content": "小明"}
    assert events[-1] == {"done": True}

    messages = mock_stream.call_args[0][0]
    assert messages == [
        {"role": "system", "content": "你是助手"},
        {"role": "user", "content": "我叫小明"},
        {"role": "assistant", "content": "你好小明！"},
        {"role": "user", "content": "我叫什么？"},
    ]


@patch("app.api.routes.chat.chat_completion_stream")
def test_chat_stream_llm_service_error(mock_stream, client: TestClient) -> None:
    mock_stream.side_effect = LLMServiceError("DeepSeek API 调用失败")

    response = client.post("/chat/stream", json={"message": "你好"})

    assert response.status_code == 200
    events = parse_sse_events(response.text)
    assert "error" in events[0]
    assert "DeepSeek API 调用失败" in events[0]["error"]
