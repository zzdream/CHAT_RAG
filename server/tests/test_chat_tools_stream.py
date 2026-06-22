"""工具注册表与 Function Calling 接口测试"""

import json
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.services.agent.function_calling import iter_function_calling_events
from app.services.tools.registry import execute_tool


def parse_sse_events(text: str) -> list[dict]:
    events: list[dict] = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("data: "):
            events.append(json.loads(line[6:]))
    return events


def test_execute_tool_calculator() -> None:
    assert execute_tool("calculator", '{"expression": "2 + 3"}') == "5"


def test_execute_tool_formatter() -> None:
    assert execute_tool("text_formatter", '{"text": "hi", "format_type": "uppercase"}') == "HI"


def test_execute_tool_unknown() -> None:
    try:
        execute_tool("unknown_tool", "{}")
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "未知工具" in str(exc)


@patch("app.services.agent.function_calling.get_openai_client")
def test_function_calling_loop_with_tool(mock_get_client) -> None:
    client = MagicMock()
    mock_get_client.return_value = client

    tool_call = MagicMock()
    tool_call.id = "call_1"
    tool_call.function.name = "calculator"
    tool_call.function.arguments = '{"expression": "1+2"}'

    first_message = MagicMock()
    first_message.content = None
    first_message.tool_calls = [tool_call]

    second_message = MagicMock()
    second_message.content = "1+2 等于 3"
    second_message.tool_calls = None

    first_response = MagicMock()
    first_response.choices = [MagicMock(message=first_message)]
    first_response.usage = MagicMock(
        prompt_tokens=10, completion_tokens=5, total_tokens=15
    )

    second_response = MagicMock()
    second_response.choices = [MagicMock(message=second_message)]
    second_response.usage = MagicMock(
        prompt_tokens=20, completion_tokens=8, total_tokens=28
    )

    client.chat.completions.create.side_effect = [first_response, second_response]

    events = list(
        iter_function_calling_events("计算 1+2", settings=MagicMock(deepseek_api_key="sk-test"))
    )

    assert events[0]["tool_call"]["name"] == "calculator"
    assert events[1]["tool_result"]["result"] == "3"
    assert events[2]["content"] == "1+2 等于 3"
    assert events[3]["usage"]["total_tokens"] == 28


@patch("app.api.routes.chat_tools.iter_function_calling_events")
def test_tools_stream_sse(mock_iter, client: TestClient) -> None:
    mock_iter.return_value = iter(
        [
            {"tool_call": {"id": "c1", "name": "calculator", "arguments": '{"expression":"1+2"}'}},
            {"tool_result": {"id": "c1", "name": "calculator", "result": "3"}},
            {"content": "结果是 3"},
            {"usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}},
        ]
    )

    response = client.post("/chat/tools/stream", json={"message": "1+2 等于多少"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

    events = parse_sse_events(response.text)
    assert "tool_call" in events[0]
    assert "tool_result" in events[1]
    assert events[2] == {"content": "结果是 3"}
    assert events[-1] == {"done": True}


def test_tools_stream_without_api_key(client: TestClient) -> None:
    with patch("app.api.routes.chat_tools.get_settings") as mock_get_settings:
        mock_get_settings.return_value.deepseek_api_key = ""

        response = client.post("/chat/tools/stream", json={"message": "你好"})

    assert response.status_code == 500
    assert "DEEPSEEK_API_KEY" in response.json()["detail"]
