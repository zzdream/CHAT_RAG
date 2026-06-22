"""
Function Calling 练习接口 —— Phase 3 新增，不影响 POST /chat/stream。
"""

import json
from collections.abc import Iterator

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.config import get_settings
from app.config_tools import get_tools_settings
from app.core.limiter import limiter
from app.schemas.chat_tools import ToolsChatRequest
from app.services.agent.function_calling import iter_function_calling_events
from app.services.llm import LLMConfigError, LLMServiceError

router = APIRouter(prefix="/chat/tools", tags=["chat-tools"])

SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


def format_sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def iter_tools_stream(payload: ToolsChatRequest) -> Iterator[str]:
    try:
        history = [{"role": item.role, "content": item.content} for item in payload.history]

        for event in iter_function_calling_events(
            payload.message,
            payload.system,
            history,
            model=payload.model,
            temperature=payload.temperature,
        ):
            yield format_sse(event)
            if "error" in event:
                return

        yield format_sse({"done": True})
    except LLMConfigError as exc:
        yield format_sse({"error": str(exc)})
    except LLMServiceError as exc:
        yield format_sse({"error": str(exc)})


def tools_rate_limit() -> str:
    settings = get_settings()
    tools_settings = get_tools_settings()
    if not settings.rate_limit_enabled:
        return "1000/second"
    return tools_settings.rate_limit_tools


@router.post("/stream")
@limiter.limit(tools_rate_limit)
def create_tools_stream(request: Request, payload: ToolsChatRequest) -> StreamingResponse:
    """
    POST /chat/tools/stream —— Function Calling 流式接口（SSE）

    在普通聊天基础上，支持 calculator / text_formatter 工具调用。
    SSE 事件除 content / usage / done / error 外，还有：
      tool_call  — 模型决定调用工具
      tool_result — 工具执行结果
    """
    settings = get_settings()
    if not settings.deepseek_api_key:
        raise HTTPException(status_code=500, detail="DEEPSEEK_API_KEY 未配置，请在 .env 中设置")

    return StreamingResponse(
        iter_tools_stream(payload),
        media_type="text/event-stream",
        headers=SSE_HEADERS,
    )
