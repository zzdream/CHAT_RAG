"""
Phase 2 RAG 配置 —— 独立于 Phase 1 的 config.py，避免改动一期配置。
"""

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

_SERVER_ROOT = Path(__file__).resolve().parent.parent


class RagSettings:
    """RAG / 知识库相关环境变量"""

    sqlite_path: str = os.getenv(
        "RAG_SQLITE_PATH",
        str(_SERVER_ROOT / "data" / "rag.db"),
    )
    chroma_persist_dir: str = os.getenv(
        "RAG_CHROMA_DIR",
        str(_SERVER_ROOT / "data" / "chroma"),
    )
    upload_dir: str = os.getenv(
        "RAG_UPLOAD_DIR",
        str(_SERVER_ROOT / "data" / "uploads"),
    )

    bge_m3_model: str = os.getenv("BGE_M3_MODEL", "BAAI/bge-m3")
    bge_m3_use_fp16: bool = os.getenv("BGE_M3_USE_FP16", "false").lower() == "true"
    bge_m3_max_length: int = int(os.getenv("BGE_M3_MAX_LENGTH", "512"))

    chunk_size: int = int(os.getenv("RAG_CHUNK_SIZE", "500"))
    chunk_overlap: int = int(os.getenv("RAG_CHUNK_OVERLAP", "50"))
    default_top_k: int = int(os.getenv("RAG_DEFAULT_TOP_K", "5"))
    max_top_k: int = int(os.getenv("RAG_MAX_TOP_K", "10"))

    allowed_extensions: frozenset[str] = frozenset(
        ext.strip().lower()
        for ext in os.getenv("RAG_ALLOWED_EXTENSIONS", ".txt,.md,.markdown").split(",")
        if ext.strip()
    )
    max_upload_bytes: int = int(os.getenv("RAG_MAX_UPLOAD_BYTES", str(5 * 1024 * 1024)))

    rate_limit_rag: str = os.getenv("RATE_LIMIT_RAG", "10/minute")

    rag_message_max_length: int = int(os.getenv("RAG_MESSAGE_MAX_LENGTH", "4000"))
    rag_history_max_messages: int = int(os.getenv("RAG_HISTORY_MAX_MESSAGES", "20"))


@lru_cache
def get_rag_settings() -> RagSettings:
    return RagSettings()
