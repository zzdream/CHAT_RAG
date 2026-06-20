"""文本分块 —— 固定窗口 + overlap。"""

from app.config_rag import get_rag_settings


def split_text(text: str) -> list[str]:
    settings = get_rag_settings()
    chunk_size = max(settings.chunk_size, 100)
    overlap = min(settings.chunk_overlap, chunk_size // 2)

    normalized = text.replace("\r\n", "\n").strip()
    if not normalized:
        return []

    chunks: list[str] = []
    start = 0
    length = len(normalized)

    while start < length:
        end = min(start + chunk_size, length)
        piece = normalized[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= length:
            break
        start = max(end - overlap, start + 1)

    return chunks
