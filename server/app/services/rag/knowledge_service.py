"""知识库业务逻辑 —— CRUD、上传、索引。"""

import shutil
from pathlib import Path

from sqlalchemy.orm import Session

from app.config_rag import get_rag_settings
from app.db.models import Document, KnowledgeBase
from app.db.session import get_session
from app.services.rag.ingest import IngestError, index_document
from app.services.rag.vector_store import delete_collection, delete_document_chunks


class KnowledgeServiceError(Exception):
    pass


def list_knowledge_bases(db: Session) -> list[KnowledgeBase]:
    return db.query(KnowledgeBase).order_by(KnowledgeBase.updated_at.desc()).all()


def get_knowledge_base(db: Session, kb_id: str) -> KnowledgeBase | None:
    return db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()


def create_knowledge_base(db: Session, name: str, description: str = "") -> KnowledgeBase:
    name = name.strip()
    if not name:
        raise KnowledgeServiceError("知识库名称不能为空")

    kb = KnowledgeBase(name=name, description=description.strip())
    db.add(kb)
    db.commit()
    db.refresh(kb)
    return kb


def delete_knowledge_base(db: Session, kb_id: str) -> None:
    kb = get_knowledge_base(db, kb_id)
    if kb is None:
        raise KnowledgeServiceError("知识库不存在")

    upload_root = Path(get_rag_settings().upload_dir) / kb_id
    if upload_root.exists():
        shutil.rmtree(upload_root, ignore_errors=True)

    delete_collection(kb_id)
    db.delete(kb)
    db.commit()


def list_documents(db: Session, kb_id: str) -> list[Document]:
    kb = get_knowledge_base(db, kb_id)
    if kb is None:
        raise KnowledgeServiceError("知识库不存在")

    return (
        db.query(Document)
        .filter(Document.knowledge_base_id == kb_id)
        .order_by(Document.created_at.desc())
        .all()
    )


def _validate_upload(filename: str, size: int) -> str:
    settings = get_rag_settings()
    suffix = Path(filename).suffix.lower()
    if suffix not in settings.allowed_extensions:
        allowed = "、".join(sorted(settings.allowed_extensions))
        raise KnowledgeServiceError(f"仅支持以下格式: {allowed}")

    if size <= 0:
        raise KnowledgeServiceError("文件不能为空")

    if size > settings.max_upload_bytes:
        max_mb = settings.max_upload_bytes / (1024 * 1024)
        raise KnowledgeServiceError(f"文件大小不能超过 {max_mb:.0f} MB")

    return suffix


def upload_document(
    db: Session,
    kb_id: str,
    filename: str,
    content: bytes,
) -> Document:
    """保存上传文件并返回 pending 状态，索引在后台异步执行。"""
    kb = get_knowledge_base(db, kb_id)
    if kb is None:
        raise KnowledgeServiceError("知识库不存在")

    _validate_upload(filename, len(content))

    doc = Document(
        knowledge_base_id=kb_id,
        filename=Path(filename).name,
        file_path="",
        file_size=len(content),
        status="pending",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    upload_dir = Path(get_rag_settings().upload_dir) / kb_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    stored_path = upload_dir / f"{doc.id}_{doc.filename}"
    stored_path.write_bytes(content)

    doc.file_path = str(stored_path)
    kb.updated_at = doc.updated_at
    db.commit()
    db.refresh(doc)
    return doc


def run_document_indexing(doc_id: str) -> None:
    """后台任务：分块 + 向量化 + 写入 Chroma。"""
    db = get_session()
    try:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if doc is None or doc.status != "pending":
            return

        stored_path = Path(doc.file_path)
        try:
            chunk_count = index_document(
                knowledge_base_id=doc.knowledge_base_id,
                document_id=doc.id,
                filename=doc.filename,
                file_path=stored_path,
            )
            doc.status = "indexed"
            doc.chunk_count = chunk_count
            doc.error_message = ""
        except (IngestError, Exception) as exc:
            doc.status = "failed"
            doc.chunk_count = 0
            doc.error_message = str(exc)

        kb = get_knowledge_base(db, doc.knowledge_base_id)
        if kb is not None:
            kb.updated_at = doc.updated_at

        db.commit()
    finally:
        db.close()


def delete_document(db: Session, doc_id: str) -> None:
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if doc is None:
        raise KnowledgeServiceError("文档不存在")

    kb_id = doc.knowledge_base_id
    delete_document_chunks(kb_id, doc.id)

    file_path = Path(doc.file_path)
    if file_path.exists():
        file_path.unlink(missing_ok=True)

    db.delete(doc)
    db.commit()

    kb = get_knowledge_base(db, kb_id)
    if kb is not None:
        db.commit()
