"""LangChain Agent 接口测试"""

import json
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from langchain_core.messages import AIMessage, ToolMessage

from app.services.agent.langchain_agent import iter_langchain_agent_events


def parse_sse_events(text: str) -> list[dict]:
    events: list[dict] = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("data: "):
            events.append(json.loads(line[6:]))
    return events


@patch("app.services.agent.langchain_agent.create_langchain_agent")
def test_langchain_agent_events(mock_create_agent) -> None:
    agent = MagicMock()
    mock_create_agent.return_value = agent

    agent.stream.return_value = iter(
        [
            {
                "model": {
                    "messages": [
                        AIMessage(
                            content="",
                            tool_calls=[
                                {
                                    "name": "calculator",
                                    "args": {"expression": "1+2"},
                                    "id": "call_1",
                                    "type": "tool_call",
                                }
                            ],
                            usage_metadata={
                                "input_tokens": 10,
                                "output_tokens": 5,
                                "total_tokens": 15,
                            },
                        )
                    ]
                }
            },
            {
                "tools": {
                    "messages": [
                        ToolMessage(
                            content="3",
                            name="calculator",
                            tool_call_id="call_1",
                        )
                    ]
                }
            },
            {
                "model": {
                    "messages": [
                        AIMessage(
                            content="1+2 等于 3",
                            usage_metadata={
                                "input_tokens": 20,
                                "output_tokens": 8,
                                "total_tokens": 28,
                            },
                        )
                    ]
                }
            },
        ]
    )

    events = list(
        iter_langchain_agent_events(
            "计算 1+2",
            settings=MagicMock(deepseek_api_key="sk-test"),
        )
    )

    mock_create_agent.assert_called_once()
    assert mock_create_agent.call_args.kwargs["knowledge_base_id"] is None

    assert events[0]["tool_call"]["name"] == "calculator"
    assert events[1]["tool_result"]["result"] == "3"
    assert events[2]["content"] == "1+2 等于 3"
    assert events[3]["usage"]["total_tokens"] == 43


@patch("app.api.routes.chat_agent.iter_langchain_agent_events")
def test_agent_stream_sse(mock_iter, client: TestClient) -> None:
    mock_iter.return_value = iter(
        [
            {"tool_call": {"id": "c1", "name": "calculator", "arguments": '{"expression":"1+2"}'}},
            {"tool_result": {"id": "c1", "name": "calculator", "result": "3"}},
            {"content": "结果是 3"},
            {"usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}},
        ]
    )

    response = client.post("/chat/agent/stream", json={"message": "1+2 等于多少"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

    events = parse_sse_events(response.text)
    assert "tool_call" in events[0]
    assert "tool_result" in events[1]
    assert events[2] == {"content": "结果是 3"}
    assert events[-1] == {"done": True}


def test_agent_stream_without_api_key(client: TestClient) -> None:
    with patch("app.api.routes.chat_agent.get_settings") as mock_get_settings:
        mock_get_settings.return_value.deepseek_api_key = ""

        response = client.post("/chat/agent/stream", json={"message": "你好"})

    assert response.status_code == 500
    assert "DEEPSEEK_API_KEY" in response.json()["detail"]
