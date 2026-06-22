"""
RAG 检索工具 —— 包装 retrieve()，供 LangChain Agent 调用。
"""

from contextvars import ContextVar
from typing import Any

from app.config_rag import get_rag_settings
from app.services.rag.embedding import EmbeddingError
from app.services.rag.prompt import build_context
from app.services.rag.retrieve import RetrievedChunk, retrieve

RagSourceRecord = dict[str, Any]

_rag_sources_buffer: ContextVar[list[RagSourceRecord] | None] = ContextVar(
    "_rag_sources_buffer",
    default=None,
)


def set_rag_sources_buffer() -> list[RagSourceRecord]:
    """为当前请求创建 sources 收集器，返回可写入的列表。"""
    buffer: list[RagSourceRecord] = []
    _rag_sources_buffer.set(buffer)
    return buffer


def get_rag_sources_buffer() -> list[RagSourceRecord] | None:
    return _rag_sources_buffer.get()


def chunk_to_source(chunk: RetrievedChunk) -> RagSourceRecord:
    return {
        "document_id": chunk.document_id,
        "filename": chunk.filename,
        "chunk_index": chunk.chunk_index,
        "content": chunk.content,
        "score": chunk.score,
    }


def search_knowledge_base(knowledge_base_id: str, query: str, top_k: int) -> str:
    """检索知识库并返回格式化文本，同时写入 sources buffer。"""
    try:
        chunks = retrieve(knowledge_base_id, query, top_k)
    except EmbeddingError as exc:
        return f"检索失败: {exc}"

    buffer = _rag_sources_buffer.get()
    if buffer is not None:
        for chunk in chunks:
            buffer.append(chunk_to_source(chunk))

    if not chunks:
        return "未检索到相关资料。"
    return build_context(chunks)


def resolve_rag_top_k(top_k: int | None) -> int:
    rag_settings = get_rag_settings()
    effective = top_k or rag_settings.default_top_k
    return min(effective, rag_settings.max_top_k)
