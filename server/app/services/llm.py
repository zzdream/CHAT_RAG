"""
LLM 调用服务层 —— 类似前端的 api/chat.ts + 业务逻辑

这一层不处理 HTTP 请求，只负责：
1. 创建 OpenAI SDK 客户端（DeepSeek 兼容 OpenAI 接口格式）
2. 组装 messages 数组
3. 调用 DeepSeek 并流式返回 token

分层对应关系（类比前端）：
  routes/chat.py  →  接口路由（Controller）
  services/llm.py →  业务服务（Service / api 封装）
  schemas/chat.py →  类型定义（Types / DTO）
"""

from collections.abc import Iterator
from functools import lru_cache
from typing import Any

from openai import APIError, OpenAI

from app.config import Settings, get_settings


# 自定义异常 —— 类似前端 throw new Error('xxx')，但更细分错误类型； Exception 是 Python 里 所有普通异常的基类（父类）。
# class LLMServiceError(Exception): 类似 JS 里：class LLMServiceError extends Error {}
# pass 是 Python 的 占位符，表示「这里什么都不做，但语法上需要有一行代码」。Python 的 class 下面 不能为空，必须至少有一行语句。如果类里暂时不需要写任何逻辑，就写 pass：
class LLMServiceError(Exception):  # 定义一个新的错误类型，它本质上就是一种「异常」，可以用 raise 抛出，用 try/except 捕获。
    """LLM 调用过程中的通用错误"""
    pass


class LLMConfigError(LLMServiceError):
    """配置错误，比如 API Key 没填"""
    pass

# @lru_cache 是 Python 自带的 函数结果缓存装饰器，意思是：相同参数调用时，直接返回上次的结果，不再重复执行函数体。
@lru_cache
def get_openai_client(settings: Settings | None = None) -> OpenAI:
    """
    创建 OpenAI SDK 客户端，指向 DeepSeek

    DeepSeek 兼容 OpenAI API，所以只需改 base_url 和 api_key，
    用法和调 OpenAI 完全一样。类似 axios.create({ baseURL, headers })
    """
    config = settings or get_settings()
    if not config.deepseek_api_key:
        raise LLMConfigError("DEEPSEEK_API_KEY 未配置，请在 .env 中设置")

    return OpenAI(
        api_key=config.deepseek_api_key,
        base_url=config.deepseek_base_url,
    )


def build_messages(
    user_message: str,
    system_prompt: str | None = None,
    history: list[dict[str, str]] | None = None,
) -> list[dict[str, str]]:
    """
    组装 LLM 需要的 messages 数组

    OpenAI/DeepSeek 的对话格式：
    [
      { "role": "system", "content": "系统提示" },      # 可选
      { "role": "user", "content": "..." },             # 历史
      { "role": "assistant", "content": "..." },        # 历史
      { "role": "user", "content": "当前用户输入" }
    ]
    """
    config = get_settings()
    messages: list[dict[str, str]] = []

    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    if history:
        max_messages = config.chat_history_max_messages
        trimmed = history[-max_messages:] if len(history) > max_messages else history
        messages.extend(trimmed)

    messages.append({"role": "user", "content": user_message})
    return messages


def chat_completion_stream(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    temperature: float | None = None,
    settings: Settings | None = None,
    usage_out: list[dict[str, int]] | None = None,
) -> Iterator[str]:
    """
    流式调用 DeepSeek —— 核心函数

    stream=True 时，API 不会一次返回完整回复，而是一个 token 一个 token 地推送。
    本函数用 yield 逐个产出 token（类似 JS 的 async function* + yield）。

    调用方（routes/chat.py）拿到每个 token 后，包装成 SSE 格式推给前端。

    参数说明：
      messages  — 对话历史（build_messages 的返回值）
      model     — 模型名，默认读 .env 里的 DEEPSEEK_MODEL
      settings  — 配置对象，一般不用传

    返回值 Iterator[str]：
      每次 yield 一个字符串片段，比如 "你"、"好"、"！"
    """
    config = settings or get_settings()
    client = get_openai_client(config)
    target_model = model or config.deepseek_model
    target_temperature = (
        temperature if temperature is not None else config.chat_default_temperature
    )

    try:
        # 调用 DeepSeek Chat Completions API（流式模式）
        stream = client.chat.completions.create(
            model=target_model,
            messages=messages,
            temperature=target_temperature,
            stream=True,  # 关键：开启流式，false 则等全部生成完才返回
            stream_options={"include_usage": True},  # 流结束时返回 token 用量
        )

        # for...in 遍历流式响应的每个 chunk（数据块）
        for chunk in stream:
            # delta.content 是本 chunk 新增的文本片段（可能为空字符串）
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta  # 产出 token，调用方立即收到

            if usage_out is not None and chunk.usage is not None:
                usage_out.append(_normalize_usage(chunk.usage))

    except APIError as exc:
        # DeepSeek 返回 401/429 等错误时抛出自定义异常
        raise LLMServiceError(f"DeepSeek API 调用失败: {exc.message}") from exc


def _normalize_usage(usage: Any) -> dict[str, int]:
    """把 OpenAI SDK 的 usage 对象转成可 JSON 序列化的字典"""
    return {
        "prompt_tokens": int(usage.prompt_tokens or 0),
        "completion_tokens": int(usage.completion_tokens or 0),
        "total_tokens": int(usage.total_tokens or 0),
    }
