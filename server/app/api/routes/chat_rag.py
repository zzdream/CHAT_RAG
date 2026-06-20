"""RAG 流式问答 API —— Phase 2 新增，不影响 POST /chat/stream。"""

import json
from collections.abc import Iterator

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.config_rag import get_rag_settings
from app.core.limiter import limiter
from app.db import get_db
from app.schemas.chat_rag import RagChatRequest, RagSourceOut
from app.services.llm import (
    LLMConfigError,
    LLMServiceError,
    chat_completion_stream,
)
from app.services.rag.embedding import EmbeddingError
from app.services.rag.knowledge_service import get_knowledge_base
from app.services.rag.prompt import build_rag_messages
from app.services.rag.retrieve import retrieve

router = APIRouter(prefix="/chat/rag", tags=["chat-rag"])

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


def format_sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def iter_rag_stream(payload: RagChatRequest, db: Session) -> Iterator[str]:
    rag_settings = get_rag_settings()

    kb = get_knowledge_base(db, payload.knowledge_base_id)
    if kb is None:
        yield format_sse({"error": "知识库不存在"})
        return

    indexed_count = sum(1 for doc in kb.documents if doc.status == "indexed")
    if indexed_count == 0:
        yield format_sse({"error": "该知识库暂无已索引文档，请先上传并成功索引"})
        return

    top_k = payload.top_k or rag_settings.default_top_k
    top_k = min(top_k, rag_settings.max_top_k)

    try:
        chunks = retrieve(payload.knowledge_base_id, payload.message, top_k)
        sources = [
            RagSourceOut(
                document_id=chunk.document_id,
                filename=chunk.filename,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                score=chunk.score,
            ).model_dump()
            for chunk in chunks
        ]
        yield format_sse({"sources": sources})

        history = [{"role": item.role, "content": item.content} for item in payload.history]
        messages = build_rag_messages(
            payload.message,
            chunks,
            history,
            max_history=rag_settings.rag_history_max_messages,
        )

        usage_events: list[dict[str, int]] = []
        for token in chat_completion_stream(
            messages,
            model=payload.model,
            temperature=payload.temperature,
            usage_out=usage_events,
        ):
            yield format_sse({"content": token})

        if usage_events:
            yield format_sse({"usage": usage_events[-1]})

        yield format_sse({"done": True})
    except EmbeddingError as exc:
        yield format_sse({"error": str(exc)})
    except LLMConfigError as exc:
        yield format_sse({"error": str(exc)})
    except LLMServiceError as exc:
        yield format_sse({"error": str(exc)})


def rag_rate_limit() -> str:
    settings = get_settings()
    rag_settings = get_rag_settings()
    if not settings.rate_limit_enabled:
        return "1000/second"
    return rag_settings.rate_limit_rag


@router.post("/stream")
@limiter.limit(rag_rate_limit)
def create_rag_stream(
    request: Request,
    payload: RagChatRequest,
    db: Session = Depends(get_db),
) -> StreamingResponse:
    settings = get_settings()
    if not settings.deepseek_api_key:
        raise HTTPException(status_code=500, detail="DEEPSEEK_API_KEY 未配置，请在 .env 中设置")

    return StreamingResponse(
        iter_rag_stream(payload, db),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )
