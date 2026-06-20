"""Chroma 向量库封装 —— 每个知识库一个 collection。"""

import re
from functools import lru_cache

import chromadb

from app.config_rag import get_rag_settings


def _collection_name(knowledge_base_id: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9_]", "_", knowledge_base_id)
    return f"kb_{safe}"


@lru_cache
def get_chroma_client() -> chromadb.ClientAPI:
    settings = get_rag_settings()
    return chromadb.PersistentClient(path=settings.chroma_persist_dir)


def get_collection(knowledge_base_id: str) -> chromadb.Collection:
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=_collection_name(knowledge_base_id),
        metadata={"hnsw:space": "cosine"},
    )


def delete_collection(knowledge_base_id: str) -> None:
    client = get_chroma_client()
    name = _collection_name(knowledge_base_id)
    try:
        client.delete_collection(name)
    except Exception:
        pass


def upsert_chunks(
    knowledge_base_id: str,
    *,
    ids: list[str],
    documents: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict[str, str | int | float]],
) -> None:
    collection = get_collection(knowledge_base_id)
    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )


def delete_document_chunks(knowledge_base_id: str, document_id: str) -> None:
    collection = get_collection(knowledge_base_id)
    try:
        collection.delete(where={"document_id": document_id})
    except Exception:
        pass


def query_chunks(
    knowledge_base_id: str,
    query_embedding: list[float],
    top_k: int,
) -> dict:
    collection = get_collection(knowledge_base_id)
    count = collection.count()
    if count == 0:
        return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

    n = min(top_k, count)
    return collection.query(
        query_embeddings=[query_embedding],
        n_results=n,
        include=["documents", "metadatas", "distances"],
    )
