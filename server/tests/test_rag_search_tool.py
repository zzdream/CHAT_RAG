"""rag_search 工具单元测试"""

from unittest.mock import patch

import pytest

from app.services.rag.retrieve import RetrievedChunk
from app.services.tools.rag_search import (
    resolve_rag_top_k,
    search_knowledge_base,
    set_rag_sources_buffer,
)


def test_resolve_rag_top_k_caps_at_max() -> None:
    with patch("app.services.tools.rag_search.get_rag_settings") as mock_settings:
        mock_settings.return_value.default_top_k = 5
        mock_settings.return_value.max_top_k = 10
        assert resolve_rag_top_k(None) == 5
        assert resolve_rag_top_k(20) == 10


@patch("app.services.tools.rag_search.retrieve")
def test_search_knowledge_base_collects_sources(mock_retrieve) -> None:
    mock_retrieve.return_value = [
        RetrievedChunk(
            document_id="doc-1",
            filename="a.txt",
            chunk_index=0,
            content="hello world",
            score=0.9,
        )
    ]
    buffer = set_rag_sources_buffer()

    result = search_knowledge_base("kb-1", "hello", 3)

    assert "hello world" in result
    assert len(buffer) == 1
    assert buffer[0]["filename"] == "a.txt"


@patch("app.services.tools.rag_search.retrieve")
def test_search_knowledge_base_empty(mock_retrieve) -> None:
    mock_retrieve.return_value = []
    set_rag_sources_buffer()

    result = search_knowledge_base("kb-1", "missing", 3)

    assert result == "未检索到相关资料。"
