"""
POST /chat/agent/stream 的请求体 —— LangChain Agent 接口。
"""

from pydantic import Field

from app.schemas.chat import ChatRequest


class AgentChatRequest(ChatRequest):
    """
    LangChain Agent 聊天请求 —— 复用 ChatRequest 的校验规则。

    可选 knowledge_base_id：传入后 Agent 可调用 rag_search 检索该知识库。
    """

    knowledge_base_id: str | None = Field(
        default=None,
        description="可选知识库 ID，启用 rag_search 工具",
    )
    top_k: int | None = Field(
        default=None,
        ge=1,
        le=20,
        description="rag_search 检索条数，默认读 RAG 配置",
    )
