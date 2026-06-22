"""
POST /chat/tools/stream 的请求体 —— Phase 3 Function Calling 练习接口。
"""

from app.schemas.chat import ChatHistoryMessage, ChatRequest


class ToolsChatRequest(ChatRequest):
    """
    工具调用聊天请求 —— 复用 ChatRequest 的校验规则。

    与 POST /chat/stream 字段一致：message、system、history、temperature、model。
    """

    pass
