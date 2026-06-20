"""
测试公共配置 —— 在所有测试 import app 之前设置环境变量
"""

import os
import tempfile

# 测试用假 Key，避免读真实 .env；真实 DeepSeek 调用一律 mock
os.environ.setdefault("DEEPSEEK_API_KEY", "sk-test-key-for-pytest")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")

_rag_test_dir = tempfile.mkdtemp(prefix="studyllm_rag_test_")
os.environ.setdefault("RAG_SQLITE_PATH", os.path.join(_rag_test_dir, "rag.db"))
os.environ.setdefault("RAG_CHROMA_DIR", os.path.join(_rag_test_dir, "chroma"))
os.environ.setdefault("RAG_UPLOAD_DIR", os.path.join(_rag_test_dir, "uploads"))

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.config_rag import get_rag_settings
from app.schemas.chat import _chat_field_limits
from app.schemas.chat_rag import _rag_field_limits
from app.services import llm


@pytest.fixture
def client() -> TestClient:
    from main import app

    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_cached_settings() -> None:
    """每个测试前后清配置缓存，避免 monkeypatch 互相影响。"""
    import app.db.session as session_module

    get_settings.cache_clear()
    get_rag_settings.cache_clear()
    _chat_field_limits.cache_clear()
    _rag_field_limits.cache_clear()
    llm.get_openai_client.cache_clear()
    session_module._engine = None
    session_module._SessionLocal = None

    from app.services.rag.vector_store import get_chroma_client

    get_chroma_client.cache_clear()
    yield
    get_settings.cache_clear()
    get_rag_settings.cache_clear()
    _chat_field_limits.cache_clear()
    _rag_field_limits.cache_clear()
    llm.get_openai_client.cache_clear()
    session_module._engine = None
    session_module._SessionLocal = None
    get_chroma_client.cache_clear()
