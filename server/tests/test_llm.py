"""LLM 服务层单元测试"""

from unittest.mock import MagicMock, patch

from app.services.llm import build_messages


def test_build_messages_single_turn() -> None:
    messages = build_messages("你好")

    assert messages == [{"role": "user", "content": "你好"}]


def test_build_messages_with_system_and_history() -> None:
    messages = build_messages(
        "继续",
        "你是助教",
        [
            {"role": "user", "content": "问题一"},
            {"role": "assistant", "content": "回答一"},
        ],
    )

    assert messages == [
        {"role": "system", "content": "你是助教"},
        {"role": "user", "content": "问题一"},
        {"role": "assistant", "content": "回答一"},
        {"role": "user", "content": "继续"},
    ]


def test_build_messages_trims_history() -> None:
    mock_settings = MagicMock(chat_history_max_messages=2)

    with patch("app.services.llm.get_settings", return_value=mock_settings):
        messages = build_messages(
            "当前",
            history=[
                {"role": "user", "content": "旧1"},
                {"role": "assistant", "content": "旧2"},
                {"role": "user", "content": "旧3"},
            ],
        )

    assert messages == [
        {"role": "assistant", "content": "旧2"},
        {"role": "user", "content": "旧3"},
        {"role": "user", "content": "当前"},
    ]
