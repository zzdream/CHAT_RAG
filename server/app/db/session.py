"""SQLAlchemy 引擎与会话 —— RAG 元数据（知识库、文档）。"""

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config_rag import get_rag_settings


class Base(DeclarativeBase):
    pass


_engine = None
_SessionLocal = None


def _ensure_engine() -> None:
    global _engine, _SessionLocal
    if _engine is not None:
        return

    db_path = Path(get_rag_settings().sqlite_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    _engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    _SessionLocal = sessionmaker(bind=_engine, autocommit=False, autoflush=False)


def init_db() -> None:
    from app.db import models  # noqa: F401

    _ensure_engine()
    Base.metadata.create_all(bind=_engine)


def get_db() -> Generator[Session, None, None]:
    _ensure_engine()
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_session() -> Session:
    """创建独立 DB 会话（后台任务使用）。"""
    _ensure_engine()
    return _SessionLocal()
