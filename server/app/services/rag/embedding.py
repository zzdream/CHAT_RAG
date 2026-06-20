"""BGE-M3 本地向量化 —— 懒加载，仅 RAG 模块使用。"""

from functools import lru_cache
from pathlib import Path
from typing import Any

from app.config_rag import get_rag_settings

_model: Any | None = None


class EmbeddingError(Exception):
    """Embedding 模型加载或推理失败"""


def _resolve_model_path(model_name: str) -> str:
    """
    优先使用本地已缓存的模型快照，避免 hf-mirror 拉取仓库里的 junk 文件（如 .DS_Store）导致 403。
    """
    if model_name.startswith(("./", "/", "~")):
        return str(Path(model_name).expanduser())

    hub_name = model_name if model_name.startswith("models--") else f"models--{model_name.replace('/', '--')}"
    snapshots_dir = Path.home() / ".cache/huggingface/hub" / hub_name / "snapshots"
    if not snapshots_dir.is_dir():
        return model_name

    weight_names = ("pytorch_model.bin", "model.safetensors")
    candidates = sorted(snapshots_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
    for snapshot in candidates:
        if snapshot.is_dir() and any((snapshot / name).exists() for name in weight_names):
            return str(snapshot)

    return model_name


def _load_model() -> Any:
    global _model
    if _model is not None:
        return _model

    settings = get_rag_settings()
    try:
        from FlagEmbedding import BGEM3FlagModel
    except ImportError as exc:
        raise EmbeddingError(
            "未安装 FlagEmbedding，请执行: pip install FlagEmbedding"
        ) from exc

    model_path = _resolve_model_path(settings.bge_m3_model)
    _model = BGEM3FlagModel(
        model_path,
        use_fp16=settings.bge_m3_use_fp16,
    )
    return _model


@lru_cache
def embedding_dimension() -> int:
    """BGE-M3 dense 向量维度"""
    return 1024


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    settings = get_rag_settings()
    model = _load_model()

    try:
        output = model.encode(
            texts,
            batch_size=min(8, len(texts)),
            max_length=settings.bge_m3_max_length,
            return_dense=True,
            return_sparse=False,
            return_colbert_vecs=False,
        )
    except Exception as exc:
        raise EmbeddingError(f"向量化失败: {exc}") from exc

    vectors: list[list[float]] = []
    for vec in output["dense_vecs"]:
        if hasattr(vec, "tolist"):
            vectors.append(vec.tolist())
        else:
            vectors.append(list(vec))
    return vectors


def embed_query(query: str) -> list[float]:
    return embed_texts([query])[0]
