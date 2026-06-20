"""文档入库：解析 → 分块 → 向量化 → 写入 Chroma。"""

from pathlib import Path

from app.services.rag.chunking import split_text
from app.services.rag.embedding import embed_texts
from app.services.rag.vector_store import delete_document_chunks, upsert_chunks


class IngestError(Exception):
    pass


def read_text_file(file_path: Path) -> str:
    suffix = file_path.suffix.lower()
    if suffix not in {".txt", ".md", ".markdown"}:
        raise IngestError(f"不支持的文件类型: {suffix}")

    for encoding in ("utf-8", "utf-8-sig", "gbk"):
        try:
            return file_path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue

    raise IngestError("无法识别文件编码，请使用 UTF-8 文本")


def index_document(
    *,
    knowledge_base_id: str,
    document_id: str,
    filename: str,
    file_path: Path,
) -> int:
    text = read_text_file(file_path)
    chunks = split_text(text)
    if not chunks:
        raise IngestError("文档内容为空")

    delete_document_chunks(knowledge_base_id, document_id)

    embeddings = embed_texts(chunks)
    ids = [f"{document_id}_chunk_{index}" for index in range(len(chunks))]
    metadatas = [
        {
            "document_id": document_id,
            "filename": filename,
            "chunk_index": index,
        }
        for index in range(len(chunks))
    ]

    upsert_chunks(
        knowledge_base_id,
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    return len(chunks)
