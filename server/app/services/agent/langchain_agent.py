"""
LangChain Agent 编排 —— 使用 create_agent + tool binding。

与 function_calling.py 的区别：
- 这里由 LangChain 管理 ReAct 循环（model → tools → model …）
- 工具通过 @tool 装饰器绑定，而非手写 OpenAI tools schema
"""

import json
from collections.abc import Iterator
from typing import Any

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.errors import GraphRecursionError

from app.config import Settings, get_settings
from app.config_agent import AgentSettings, get_agent_settings
from app.config_retry import get_retry_settings
from app.services.agent.tool_registry import get_agent_tools
from app.services.llm import LLMConfigError, LLMServiceError
from app.services.llm_retry import get_chat_openai_max_retries, is_retryable_api_error
from app.services.tools.rag_search import get_rag_sources_buffer, set_rag_sources_buffer


class AgentRunError(LLMServiceError):
    """LangChain Agent 运行过程中的错误"""


def _content_to_str(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text", "")))
        return "".join(parts)
    return str(content)


def _accumulate_usage(message: AIMessage, usage: dict[str, int]) -> None:
    metadata = message.usage_metadata
    if not metadata:
        return
    usage["prompt_tokens"] += int(metadata.get("input_tokens") or 0)
    usage["completion_tokens"] += int(metadata.get("output_tokens") or 0)
    usage["total_tokens"] += int(metadata.get("total_tokens") or 0)


def _resolve_system_prompt(
    system_prompt: str | None,
    agent_config: AgentSettings,
    *,
    knowledge_base_name: str | None = None,
) -> str:
    base = system_prompt or agent_config.agent_default_system
    if knowledge_base_name:
        suffix = agent_config.agent_rag_system_suffix.format(kb_name=knowledge_base_name)
        return f"{base}\n{suffix}"
    return base


def build_langchain_messages(
    user_message: str,
    history: list[dict[str, str]] | None = None,
    *,
    settings: Settings | None = None,
) -> list[BaseMessage]:
    """把多轮 history 转为 LangChain messages（不含 system，system 由 create_agent 处理）。"""
    config = settings or get_settings()
    messages: list[BaseMessage] = []

    if history:
        max_messages = config.chat_history_max_messages
        trimmed = history[-max_messages:] if len(history) > max_messages else history
        for item in trimmed:
            role = item.get("role")
            content = item.get("content")
            if not isinstance(content, str):
                continue
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "assistant":
                messages.append(AIMessage(content=content))

    messages.append(HumanMessage(content=user_message))
    return messages


def create_langchain_agent(
    *,
    system_prompt: str,
    model: str | None = None,
    temperature: float | None = None,
    settings: Settings | None = None,
    knowledge_base_id: str | None = None,
    top_k: int | None = None,
):
    """创建 LangChain ReAct Agent（内部基于 LangGraph 循环）。"""
    config = settings or get_settings()
    if not config.deepseek_api_key:
        raise LLMConfigError("DEEPSEEK_API_KEY 未配置，请在 .env 中设置")

    llm = ChatOpenAI(
        model=model or config.deepseek_model,
        api_key=config.deepseek_api_key,
        base_url=config.deepseek_base_url,
        temperature=(
            temperature if temperature is not None else config.chat_default_temperature
        ),
        max_retries=get_chat_openai_max_retries(get_retry_settings()),
    )
    tools = get_agent_tools(knowledge_base_id, top_k)
    return create_agent(llm, tools, system_prompt=system_prompt)


def iter_langchain_agent_events(
    user_message: str,
    system_prompt: str | None = None,
    history: list[dict[str, str]] | None = None,
    *,
    model: str | None = None,
    temperature: float | None = None,
    settings: Settings | None = None,
    agent_settings: AgentSettings | None = None,
    knowledge_base_id: str | None = None,
    top_k: int | None = None,
    knowledge_base_name: str | None = None,
) -> Iterator[dict[str, Any]]:
    """
    运行 LangChain Agent 并产出 SSE 事件 payload。

    事件类型：
      tool_call / tool_result / sources / content / usage / error
    """
    config = settings or get_settings()
    agent_config = agent_settings or get_agent_settings()
    system = _resolve_system_prompt(
        system_prompt,
        agent_config,
        knowledge_base_name=knowledge_base_name,
    )

    set_rag_sources_buffer()
    emitted_source_count = 0

    try:
        agent = create_langchain_agent(
            system_prompt=system,
            model=model,
            temperature=temperature,
            settings=config,
            knowledge_base_id=knowledge_base_id,
            top_k=top_k,
        )
    except LLMConfigError:
        raise

    messages = build_langchain_messages(user_message, history, settings=config)
    run_config = {"recursion_limit": agent_config.agent_max_iterations}
    usage_totals = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    final_content: str | None = None
    retry_settings = get_retry_settings()
    max_attempts = (
        retry_settings.llm_retry_max_attempts if retry_settings.llm_retry_enabled else 1
    )

    try:
        for run_attempt in range(1, max_attempts + 1):
            emitted_any = False
            try:
                for chunk in agent.stream(
                    {"messages": messages},
                    config=run_config,
                    stream_mode="updates",
                ):
                    emitted_any = True
                    for _node, update in chunk.items():
                        for message in update.get("messages", []):
                            if isinstance(message, AIMessage):
                                _accumulate_usage(message, usage_totals)

                                if message.tool_calls:
                                    for tool_call in message.tool_calls:
                                        yield {
                                            "tool_call": {
                                                "id": tool_call["id"],
                                                "name": tool_call["name"],
                                                "arguments": json.dumps(
                                                    tool_call["args"],
                                                    ensure_ascii=False,
                                                ),
                                            }
                                        }
                                    continue

                                content = _content_to_str(message.content).strip()
                                if content:
                                    final_content = content

                            elif isinstance(message, ToolMessage):
                                tool_name = message.name or "unknown"
                                yield {
                                    "tool_result": {
                                        "id": message.tool_call_id,
                                        "name": tool_name,
                                        "result": _content_to_str(message.content),
                                    }
                                }

                                if tool_name == "rag_search":
                                    buffer = get_rag_sources_buffer() or []
                                    new_sources = buffer[emitted_source_count:]
                                    if new_sources:
                                        yield {"sources": new_sources}
                                        emitted_source_count = len(buffer)
                break
            except Exception as exc:
                if (
                    not emitted_any
                    and is_retryable_api_error(exc)
                    and run_attempt < max_attempts
                ):
                    yield {
                        "retry": {
                            "attempt": run_attempt,
                            "max_attempts": max_attempts,
                            "message": "Agent 调用暂时失败，正在重试…",
                        }
                    }
                    continue
                raise

        if final_content:
            yield {"content": final_content}
        elif not usage_totals["total_tokens"]:
            yield {"error": "Agent 未返回有效回答"}

        if usage_totals["total_tokens"] > 0:
            yield {"usage": usage_totals}

    except GraphRecursionError as exc:
        yield {
            "error": (
                f"超过最大 Agent 迭代次数（{agent_config.agent_max_iterations}）: {exc}"
            )
        }
    except Exception as exc:
        raise AgentRunError(f"LangChain Agent 运行失败: {exc}") from exc
