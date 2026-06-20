"""RAG 流式聊天 API 的请求/响应模型。"""

from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.config import get_settings
from app.config_rag import get_rag_settings
from app.validators.sensitive_words import find_sensitive_words, format_sensitive_word_error


@lru_cache
def _rag_field_limits() -> tuple[int, int, frozenset[str], int, int, int]:
    chat_settings = get_settings()
    rag_settings = get_rag_settings()
    return (
        rag_settings.rag_message_max_length,
        rag_settings.rag_history_max_messages,
        chat_settings.sensitive_words,
        rag_settings.default_top_k,
        rag_settings.max_top_k,
        chat_settings.chat_allowed_models,
    )


class RagHistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1)

    @model_validator(mode="after")
    def validate_content_rules(self) -> "RagHistoryMessage":
        max_length, _, sensitive_words, _, _, _ = _rag_field_limits()

        if len(self.content) > max_length:
            raise ValueError(f"历史消息长度不能超过 {max_length} 个字符")

        if self.role == "user":
            found = find_sensitive_words(self.content, sensitive_words)
            if found:
                raise ValueError(format_sensitive_word_error(found))

        return self


class RagChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    knowledge_base_id: str = Field(..., min_length=1)
    history: list[RagHistoryMessage] = Field(default_factory=list)
    top_k: int | None = Field(default=None, ge=1, le=20)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    model: str | None = Field(default=None)

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        max_length, _, sensitive_words, _, _, _ = _rag_field_limits()
        if len(value) > max_length:
            raise ValueError(f"消息长度不能超过 {max_length} 个字符")

        found = find_sensitive_words(value, sensitive_words)
        if found:
            raise ValueError(format_sensitive_word_error(found))
        return value

    @field_validator("history")
    @classmethod
    def validate_history_count(cls, value: list[RagHistoryMessage]) -> list[RagHistoryMessage]:
        _, max_messages, _, _, _, _ = _rag_field_limits()
        if len(value) > max_messages:
            raise ValueError(f"历史消息不能超过 {max_messages} 条")
        return value

    @field_validator("model")
    @classmethod
    def validate_model(cls, value: str | None) -> str | None:
        if value is None:
            return value

        _, _, _, _, _, allowed_models = _rag_field_limits()
        if value not in allowed_models:
            allowed = "、".join(sorted(allowed_models))
            raise ValueError(f"不支持的模型，可选：{allowed}")
        return value


class RagSourceOut(BaseModel):
    document_id: str
    filename: str
    chunk_index: int
    content: str
    score: float
