"""
聊天接口路由 —— 类似前端的 API Route Handler / Express Router

URL 映射：
  POST /chat/stream  →  流式聊天（SSE），前端实际使用的接口

文件结构说明：
  router = APIRouter(prefix="/chat")  →  这组路由都以 /chat 开头
  @router.post("/stream")               →  完整路径 = /chat/stream

装饰器 @router.post("/stream") 类似：
  router.post('/stream', handler)  // Express
"""

import json
from collections.abc import Iterator

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.config import get_settings
from app.core.limiter import limiter
from app.schemas.chat import ChatRequest
from app.services.llm import (
    LLMConfigError,
    LLMServiceError,
    build_messages,
    chat_completion_stream,
)

# 创建路由组，prefix="/chat" 表示路径前缀
router = APIRouter(prefix="/chat", tags=["chat"])

# SSE 响应需要的 HTTP 头 —— 告诉浏览器和代理「这是流式数据，不要缓存」
SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",  # 禁止 nginx 缓冲（有 nginx 时需要）
}


def format_sse(payload: dict) -> str:
    """
    把 JSON 对象格式化为 SSE 标准格式

    SSE 规定每条消息格式为：
      data: {"key": "value"}\n\n    ← 注意末尾两个换行

    前端 fetch 后按行解析，看到 data: 开头就 JSON.parse 后面的内容。
    对应前端：web/src/api/chat.ts 里的 parseSseLine()
    f"..." — f-string（格式化字符串） Python 的字符串插值，类似 JS 模板字符串：
    json.dumps(payload, ...) — 字典转 JSON 字符串  类似 JS 的 JSON.stringify(payload)。
    默认 json.dumps 会把中文转成 Unicode 转义（如 \\u4f60）：ensure_ascii=False 可保留原样中文
    """
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
    # ensure_ascii=False 保证中文不被转成 \uXXXX


def iter_chat_stream(payload: ChatRequest) -> Iterator[str]:
    """
    生成器函数：逐个产出 SSE 事件字符串

    yield 是 Python 的「生成器」关键字，类似 JS 的 async function* + yield：
      - 函数不会一次性执行完，而是每次 yield 暂停并返回值
      - 调用方用 for 循环逐个消费（FastAPI StreamingResponse 会自动处理）

    产出的事件类型（前端需识别）：
      {"content": "你"}   → 追加到聊天内容
      {"usage": {...}}    → token 用量（流结束前）
      {"done": true}      → 流结束
      {"error": "..."}    → 出错信息
    """
    try:
        # 1. 把前端 JSON 转成 LLM 需要的 messages 格式（含多轮 history）
        history = [{"role": item.role, "content": item.content} for item in payload.history]
        messages = build_messages(payload.message, payload.system, history)

        usage_events: list[dict[str, int]] = []

        # 2. 流式调用 DeepSeek，每收到一个 token 就推送给前端
        for token in chat_completion_stream(
            messages,
            model=payload.model,
            temperature=payload.temperature,
            usage_out=usage_events,
        ):
            yield format_sse({"content": token})

        if usage_events:
            yield format_sse({"usage": usage_events[-1]})

        # 3. 全部完成，发送结束标记
        yield format_sse({"done": True})
    # except 捕获异常，类似 JS 的 catch，LLMConfigError：只捕获这一种错误类型，exc：异常对象
    except LLMConfigError as exc:
        # 配置错误（如 API Key 未填）—— 通过 SSE 告诉前端，而不是抛 HTTP 500
        yield format_sse({"error": str(exc)})
    except LLMServiceError as exc:
        # DeepSeek 调用失败（如余额不足、网络错误）
        yield format_sse({"error": str(exc)})


def chat_rate_limit() -> str:
    """限流规则：可在 .env 用 RATE_LIMIT_CHAT 调整；关闭时用极高配额。"""
    settings = get_settings()
    if not settings.rate_limit_enabled:
        return "1000/second"
    return settings.rate_limit_chat


@router.post("/stream")
@limiter.limit(chat_rate_limit)
def create_chat_stream(request: Request, payload: ChatRequest) -> StreamingResponse:
    """
    POST /chat/stream —— 流式聊天接口

    参数 payload: ChatRequest
      FastAPI 自动把请求体 JSON 解析并校验为 ChatRequest 对象
      （类似 Express 里用 zod.parse(req.body)）

    返回 StreamingResponse：
      不会等全部生成完才响应，而是边生成边推送（SSE）
      media_type="text/event-stream" 告诉浏览器这是 SSE 流

    前端调用链：
      web/src/views/chat/index.vue
        → useChatStream() hook
          → streamChat() in api/chat.ts
            → fetch('/api/chat/stream')  ← Vite 代理到此接口
    """
    settings = get_settings()

    # 提前检查 API Key，没配置直接返回 HTTP 500（比流式中途报错体验更好）
    if not settings.deepseek_api_key:
        raise HTTPException(status_code=500, detail="DEEPSEEK_API_KEY 未配置，请在 .env 中设置")

    return StreamingResponse(
        iter_chat_stream(payload),       # 传入生成器，FastAPI 边读边写给客户端
        media_type="text/event-stream",  # SSE 标准 MIME 类型
        headers=SSE_HEADERS,
    )
