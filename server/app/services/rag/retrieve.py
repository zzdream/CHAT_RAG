"""检索逻辑 —— query 向量化 + Chroma top-k。"""

from dataclasses import dataclass

from app.services.rag.embedding import embed_query
from app.services.rag.vector_store import query_chunks


@dataclass
class RetrievedChunk:
    document_id: str
    filename: str
    chunk_index: int
    content: str
    score: float


def retrieve(knowledge_base_id: str, query: str, top_k: int) -> list[RetrievedChunk]:
    query_vec = embed_query(query)
    result = query_chunks(knowledge_base_id, query_vec, top_k)

    ids = result.get("ids") or [[]]
    documents = result.get("documents") or [[]]
    metadatas = result.get("metadatas") or [[]]
    distances = result.get("distances") or [[]]

    if not ids or not ids[0]:
        return []

    chunks: list[RetrievedChunk] = []
    for idx, doc_text in enumerate(documents[0]):
        meta = metadatas[0][idx] if idx < len(metadatas[0]) else {}
        distance = distances[0][idx] if idx < len(distances[0]) else 1.0
        # cosine distance: 越小越相似，转为 0~1 的 score
        score = max(0.0, 1.0 - float(distance))

        chunks.append(
            RetrievedChunk(
                document_id=str(meta.get("document_id", "")),
                filename=str(meta.get("filename", "")),
                chunk_index=int(meta.get("chunk_index", idx)),
                content=doc_text or "",
                score=round(score, 4),
            )
        )
    return chunks
