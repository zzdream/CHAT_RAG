"""
Phase 2 RAG 引导 —— 注册路由、初始化数据库，不修改 Phase 1 业务模块。
"""

from pathlib import Path

from fastapi import FastAPI

from app.api.routes import chat_rag, knowledge
from app.config_rag import get_rag_settings
from app.db import init_db


def setup_rag(app: FastAPI) -> None:
    """挂载 RAG 路由并初始化 SQLite / 数据目录。"""
    settings = get_rag_settings()
    Path(settings.chroma_persist_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.sqlite_path).parent.mkdir(parents=True, exist_ok=True)

    init_db()
    app.include_router(knowledge.router)
    app.include_router(chat_rag.router)
