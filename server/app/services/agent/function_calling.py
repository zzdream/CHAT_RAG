"""
原生 OpenAI Function Calling 循环 —— 不依赖 LangChain。

流程：
1. 发送 messages + tools 给 LLM
2. 若返回 tool_calls → 执行工具 → 把结果追加到 messages → 回到 1
3. 若返回文本 → 结束，产出最终回答
"""

import json
from collections.abc import Iterator
from typing import Any

from openai import APIError
from openai.types.chat import ChatCompletionMessage

from app.config import Settings, get_settings
from app.config_retry import get_retry_settings
from app.config_tools import ToolsSettings, get_tools_settings
from app.services.llm import LLMConfigError, LLMServiceError, get_openai_client
from app.services.llm_retry import chat_completion_create_with_retry
from app.services.tools.registry import TOOL_DEFINITIONS, execute_tool


class ToolCallingError(LLMServiceError):
    """工具调用编排过程中的错误"""


def _assistant_message_dict(message: ChatCompletionMessage) -> dict[str, Any]:
    """把 SDK 返回的 assistant message 转成 API 可接受的 dict。"""
    payload: dict[str, Any] = {"role": "assistant", "content": message.content}
    if message.tool_calls:
        payload["tool_calls"] = [
            {
                "id": tool_call.id,
                "type": "function",
                "function": {
                    "name": tool_call.function.name,
                    "arguments": tool_call.function.arguments,
                },
            }
            for tool_call in message.tool_calls
        ]
    return payload


def build_tool_messages(
    user_message: str,
    system_prompt: str | None = None,
    history: list[dict[str, str]] | None = None,
    *,
    settings: Settings | None = None,
) -> list[dict[str, Any]]:
    """组装 Function Calling 用的 messages，history 仅保留 user/assistant 文本消息。"""
    config = settings or get_settings()
    messages: list[dict[str, Any]] = []

    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    if history:
        max_messages = config.chat_history_max_messages
        trimmed = history[-max_messages:] if len(history) > max_messages else history
        for item in trimmed:
            role = item.get("role")
            content = item.get("content")
            if role in {"user", "assistant"} and isinstance(content, str):
                messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": user_message})
    return messages


def iter_function_calling_events(
    user_message: str,
    system_prompt: str | None = None,
    history: list[dict[str, str]] | None = None,
    *,
    model: str | None = None,
    temperature: float | None = None,
    settings: Settings | None = None,
    tools_settings: ToolsSettings | None = None,
) -> Iterator[dict[str, Any]]:
    """
    执行 Function Calling 循环，逐个产出 SSE 事件 payload。

    事件类型：
      {"tool_call": {"name", "arguments", "id"}}
      {"tool_result": {"name", "result", "id"}}
      {"content": "..."}           — 最终回答（完整文本）
      {"usage": {...}}             — token 用量（若有）
      {"error": "..."}             — 错误信息
    """
    config = settings or get_settings()
    tool_config = tools_settings or get_tools_settings()

    if not config.deepseek_api_key:
        raise LLMConfigError("DEEPSEEK_API_KEY 未配置，请在 .env 中设置")

    client = get_openai_client(config)
    target_model = model or config.deepseek_model
    target_temperature = (
        temperature if temperature is not None else config.chat_default_temperature
    )
    system = system_prompt or tool_config.tools_default_system
    messages = build_tool_messages(user_message, system, history, settings=config)

    last_usage: dict[str, int] | None = None
    retry_settings = get_retry_settings()
    retry_events: list[dict[str, Any]] = []

    def _notify_retry(attempt: int, max_attempts: int, exc: BaseException) -> None:
        retry_events.append(
            {
                "retry": {
                    "attempt": attempt,
                    "max_attempts": max_attempts,
                    "message": f"API 暂时不可用（{getattr(exc, 'status_code', 'unknown')}），正在重试…",
                }
            }
        )

    try:
        for _ in range(tool_config.tools_max_iterations):
            retry_events.clear()

            response = chat_completion_create_with_retry(
                client,
                settings=retry_settings,
                on_retry=_notify_retry,
                model=target_model,
                messages=messages,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto",
                temperature=target_temperature,
            )

            for event in retry_events:
                yield event

            if response.usage is not None:
                last_usage = {
                    "prompt_tokens": int(response.usage.prompt_tokens or 0),
                    "completion_tokens": int(response.usage.completion_tokens or 0),
                    "total_tokens": int(response.usage.total_tokens or 0),
                }

            message = response.choices[0].message

            if message.tool_calls:
                messages.append(_assistant_message_dict(message))

                for tool_call in message.tool_calls:
                    fn = tool_call.function
                    tool_name = fn.name
                    tool_args = fn.arguments

                    yield {
                        "tool_call": {
                            "id": tool_call.id,
                            "name": tool_name,
                            "arguments": tool_args,
                        }
                    }

                    try:
                        result = execute_tool(tool_name, tool_args)
                    except ValueError as exc:
                        result = f"工具执行失败: {exc}"

                    yield {
                        "tool_result": {
                            "id": tool_call.id,
                            "name": tool_name,
                            "result": result,
                        }
                    }

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result,
                        }
                    )
                continue

            content = message.content or ""
            if content:
                yield {"content": content}
            if last_usage is not None:
                yield {"usage": last_usage}
            return

        raise ToolCallingError(
            f"超过最大工具调用轮数（{tool_config.tools_max_iterations}）"
        )

    except LLMConfigError:
        raise
    except ToolCallingError as exc:
        yield {"error": str(exc)}
    except APIError as exc:
        raise LLMServiceError(f"DeepSeek API 调用失败: {exc.message}") from exc
    except json.JSONDecodeError as exc:
        yield {"error": f"工具参数解析失败: {exc.msg}"}
