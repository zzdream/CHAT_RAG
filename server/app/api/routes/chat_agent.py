"""
LangChain Agent 接口 —— Phase 3 新增，不影响 POST /chat/stream 与 /chat/tools/stream。
"""

import json
from collections.abc import Iterator

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.config_agent import get_agent_settings
from app.core.limiter import limiter
from app.db import get_db
from app.schemas.chat_agent import AgentChatRequest
from app.services.agent.langchain_agent import iter_langchain_agent_events
from app.services.llm import LLMConfigError, LLMServiceError
from app.services.rag.knowledge_service import get_knowledge_base

router = APIRouter(prefix="/chat/agent", tags=["chat-agent"])

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


def format_sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def iter_agent_stream(
    payload: AgentChatRequest,
    *,
    knowledge_base_name: str | None = None,
) -> Iterator[str]:
    try:
        history = [{"role": item.role, "content": item.content} for item in payload.history]

        for event in iter_langchain_agent_events(
            payload.message,
            payload.system,
            history,
            model=payload.model,
            temperature=payload.temperature,
            knowledge_base_id=payload.knowledge_base_id,
            top_k=payload.top_k,
            knowledge_base_name=knowledge_base_name,
        ):
            yield format_sse(event)
            if "error" in event:
                return

        yield format_sse({"done": True})
    except LLMConfigError as exc:
        yield format_sse({"error": str(exc)})
    except LLMServiceError as exc:
        yield format_sse({"error": str(exc)})


def agent_rate_limit() -> str:
    settings = get_settings()
    agent_settings = get_agent_settings()
    if not settings.rate_limit_enabled:
        return "1000/second"
    return agent_settings.rate_limit_agent


@router.post("/stream")
@limiter.limit(agent_rate_limit)
def create_agent_stream(
    request: Request,
    payload: AgentChatRequest,
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """
    POST /chat/agent/stream —— LangChain Agent 流式接口（SSE）

    由 LangChain create_agent 自动编排工具调用。
    基础工具：calculator、text_formatter。
    传入 knowledge_base_id 后追加 rag_search，实现文档查询 + 工具调用联合助手。
    SSE 事件：tool_call、tool_result、sources、content、usage、done、error。
    """
    settings = get_settings()
    if not settings.deepseek_api_key:
        raise HTTPException(status_code=500, detail="DEEPSEEK_API_KEY 未配置，请在 .env 中设置")

    knowledge_base_name: str | None = None
    if payload.knowledge_base_id:
        kb = get_knowledge_base(db, payload.knowledge_base_id)
        if kb is None:
            raise HTTPException(status_code=404, detail="知识库不存在")

        indexed_count = sum(1 for doc in kb.documents if doc.status == "indexed")
        if indexed_count == 0:

            def empty_kb_stream() -> Iterator[str]:
                yield format_sse({"error": "该知识库暂无已索引文档，请先上传并成功索引"})
                yield format_sse({"done": True})

            return StreamingResponse(
                empty_kb_stream(),
                media_type="text/event-stream",
                headers=SSE_HEADERS,
            )

        knowledge_base_name = kb.name

    return StreamingResponse(
        iter_agent_stream(payload, knowledge_base_name=knowledge_base_name),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )
