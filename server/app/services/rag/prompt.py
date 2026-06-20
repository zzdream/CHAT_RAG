"""RAG Prompt 组装 —— 独立于 Phase 1 的 build_messages。"""

from app.services.rag.retrieve import RetrievedChunk

RAG_SYSTEM_TEMPLATE = """你是一个知识库问答助手。请严格根据以下「参考资料」回答用户问题。
- 若资料中没有答案，请明确说明「根据现有资料无法回答」。
- 不要编造资料中不存在的信息。
- 使用中文，条理清晰。

【参考资料】
{context}
"""


def build_context(chunks: list[RetrievedChunk]) -> str:
    if not chunks:
        return "（未检索到相关资料）"

    parts: list[str] = []
    for index, chunk in enumerate(chunks, start=1):
        source = chunk.filename or chunk.document_id or "未知来源"
        parts.append(
            f"[{index}] 来源: {source}\n{chunk.content.strip()}"
        )
    return "\n\n".join(parts)


def build_rag_messages(
    user_message: str,
    chunks: list[RetrievedChunk],
    history: list[dict[str, str]] | None = None,
    *,
    max_history: int = 20,
) -> list[dict[str, str]]:
    messages: list[dict[str, str]] = [
        {
            "role": "system",
            "content": RAG_SYSTEM_TEMPLATE.format(context=build_context(chunks)),
        }
    ]

    if history:
        trimmed = history[-max_history:] if len(history) > max_history else history
        messages.extend(trimmed)

    messages.append({"role": "user", "content": user_message})
    return messages
