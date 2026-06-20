"""
请求/响应的数据模型 —— 类似前端的 TypeScript interface 或 Zod schema

Pydantic 会在接口收到 JSON 时自动：
1. 校验字段类型（message 必须是字符串）
2. 校验约束（min_length=1 表示不能为空）
3. 自定义 @field_validator（如敏感词过滤）
4. 校验失败自动返回 422 错误，不用手写 if 判断

前端对应类型见：web/src/types/chat.ts
"""

from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.config import get_settings
from app.validators.sensitive_words import find_sensitive_words, format_sensitive_word_error


@lru_cache
def _chat_field_limits() -> tuple[int, int, frozenset[str], int]:
    """读取聊天相关配置上限，缓存避免重复读 .env"""
    settings = get_settings()
    return (
        settings.chat_message_max_length,      # 单条 message 最大字符数
        settings.chat_system_max_length,     # system 提示词最大字符数
        settings.sensitive_words,            # 敏感词集合
        settings.chat_history_max_messages,  # history 最多条数（多轮对话）
        settings.chat_allowed_models,        # 允许的模型白名单
    )


class ChatHistoryMessage(BaseModel):
    """单条历史消息 —— 对应前端 ChatHistoryMessage（多轮对话用）"""

    role: Literal["user", "assistant"]  # 只能是 user 或 assistant，LLM API 规定的角色  Literal[...] 类似 TS：role: 'user' | 'assistant'
    content: str = Field(..., min_length=1)  # Field(...) 里 ... 表示必填

    # model_validator(mode="after")：整个对象字段都赋值完后，再做联合校验（可同时看 role + content）
    @model_validator(mode="after")
    def validate_content_rules(self) -> "ChatHistoryMessage":
        max_length, _, sensitive_words, _, _ = _chat_field_limits()

        if len(self.content) > max_length:
            raise ValueError(f"历史消息长度不能超过 {max_length} 个字符")

        # 历史里只校验 user 消息的敏感词；assistant 是模型自己的回复，无需再拦
        if self.role == "user":
            found = find_sensitive_words(self.content, sensitive_words)
            if found:
                raise ValueError(format_sensitive_word_error(found))

        return self


# BaseModel 定义「数据模型」的基类，类似 TypeScript 的 interface + 运行时校验
# Field 给每个字段加规则：是否必填、长度、默认值、文档说明
class ChatRequest(BaseModel):
    """
    POST /chat/stream 的请求体

    前端发送示例（多轮）：
    {
      "message": "我叫什么？",
      "system": "你是一位助手",
      "history": [
        { "role": "user", "content": "我叫小明" },
        { "role": "assistant", "content": "你好小明！" }
      ]
    }

    Field(...) 里 ... 表示必填；system 有 default=None 表示可选
    history 默认 [] 表示无历史（单轮对话）
    """

    message: str = Field(..., min_length=1, description="当前用户输入")
    system: str | None = Field(default=None, description="可选系统提示词")
    # str | None 等价于 TS 的 string | null | undefined
    history: list[ChatHistoryMessage] = Field(
        default_factory=list,  # default_factory=list 表示默认空列表，避免多个请求共享同一个 list
        description="当前消息之前的多轮对话历史",
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="采样温度，越高越发散",
    )
    model: str | None = Field(
        default=None,
        description="模型名称，不传则使用服务端默认 DEEPSEEK_MODEL",
    )
    @field_validator("message", "system") # 表示：对 message 和 system 两个字段 都做同样的校验。 Pydantic 的 @field_validator 要求校验函数必须是类方法，所以必须写 @classmethod：
    @classmethod # 表示：下面的函数是类方法，第一个参数是类本身 cls，而不是实例 self。第一个参数是 cls（类本身 ChatRequest），第二个参数是 value（要校验的值），返回值是校验后的值。
    def validate_no_sensitive_words(cls, value: str | None) -> str | None:
        if value is None:
            return value

        # _, _, sensitive_words, _ 分别是：消息长度上限、system 长度上限、敏感词集合、history 条数上限
        _, _, sensitive_words, _, _ = _chat_field_limits()
        found = find_sensitive_words(value, sensitive_words)
        if found:
            raise ValueError(format_sensitive_word_error(found))
        return value

    @field_validator("message")
    @classmethod
    def validate_message_length(cls, value: str) -> str:
        max_length, _, _, _, _ = _chat_field_limits()
        if len(value) > max_length:
            raise ValueError(f"消息长度不能超过 {max_length} 个字符")
        return value

    @field_validator("system")
    @classmethod
    def validate_system_length(cls, value: str | None) -> str | None:
        if value is None:
            return value

        _, max_length, _, _, _ = _chat_field_limits()
        if len(value) > max_length:
            raise ValueError(f"系统提示词长度不能超过 {max_length} 个字符")
        return value

    @field_validator("model")
    @classmethod
    def validate_model(cls, value: str | None) -> str | None:
        if value is None:
            return value

        _, _, _, _, allowed_models = _chat_field_limits()
        if value not in allowed_models:
            allowed = "、".join(sorted(allowed_models))
            raise ValueError(f"不支持的模型，可选：{allowed}")
        return value

    @field_validator("history")
    @classmethod
    def validate_history_count(
        cls, value: list[ChatHistoryMessage]
    ) -> list[ChatHistoryMessage]:
        # 防止前端一次传过多历史消息；超出 build_messages 里还会再截断最近 N 条
        _, _, _, max_messages, _ = _chat_field_limits()
        if len(value) > max_messages:
            raise ValueError(f"历史消息不能超过 {max_messages} 条")
        return value
