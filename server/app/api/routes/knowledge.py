"""知识库管理 API —— Phase 2 新增，不影响 /chat。"""

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db import get_db
from app.db.models import Document, KnowledgeBase
from app.schemas.knowledge import DocumentOut, KnowledgeBaseCreate, KnowledgeBaseOut
from app.services.rag.knowledge_service import (
    KnowledgeServiceError,
    create_knowledge_base,
    delete_document,
    delete_knowledge_base,
    get_knowledge_base,
    list_documents,
    list_knowledge_bases,
    run_document_indexing,
    upload_document,
)

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


def _to_kb_out(kb: KnowledgeBase) -> KnowledgeBaseOut:
    return KnowledgeBaseOut(
        id=kb.id,
        name=kb.name,
        description=kb.description,
        document_count=len(kb.documents),
        created_at=kb.created_at,
        updated_at=kb.updated_at,
    )


def _to_doc_out(doc: Document) -> DocumentOut:
    return DocumentOut(
        id=doc.id,
        knowledge_base_id=doc.knowledge_base_id,
        filename=doc.filename,
        file_size=doc.file_size,
        status=doc.status,
        chunk_count=doc.chunk_count,
        error_message=doc.error_message,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
    )


@router.get("/bases", response_model=list[KnowledgeBaseOut])
def get_bases(db: Session = Depends(get_db)) -> list[KnowledgeBaseOut]:
    bases = list_knowledge_bases(db)
    return [_to_kb_out(item) for item in bases]


@router.post("/bases", response_model=KnowledgeBaseOut)
def post_base(payload: KnowledgeBaseCreate, db: Session = Depends(get_db)) -> KnowledgeBaseOut:
    try:
        kb = create_knowledge_base(db, payload.name, payload.description)
    except KnowledgeServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_kb_out(kb)


@router.get("/bases/{kb_id}", response_model=KnowledgeBaseOut)
def get_base(kb_id: str, db: Session = Depends(get_db)) -> KnowledgeBaseOut:
    kb = get_knowledge_base(db, kb_id)
    if kb is None:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return _to_kb_out(kb)


@router.delete("/bases/{kb_id}")
def remove_base(kb_id: str, db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        delete_knowledge_base(db, kb_id)
    except KnowledgeServiceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"message": "已删除"}


@router.get("/bases/{kb_id}/documents", response_model=list[DocumentOut])
def get_documents(kb_id: str, db: Session = Depends(get_db)) -> list[DocumentOut]:
    try:
        docs = list_documents(db, kb_id)
    except KnowledgeServiceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return [_to_doc_out(item) for item in docs]


@router.post("/bases/{kb_id}/documents", response_model=DocumentOut)
async def post_document(
    kb_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> DocumentOut:
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    content = await file.read()
    try:
        doc = upload_document(db, kb_id, file.filename, content)
    except KnowledgeServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    background_tasks.add_task(run_document_indexing, doc.id)
    return _to_doc_out(doc)


@router.delete("/documents/{doc_id}")
def remove_document(doc_id: str, db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        delete_document(db, doc_id)
    except KnowledgeServiceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {"message": "已删除"}
