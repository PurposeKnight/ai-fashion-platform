from __future__ import annotations

from typing import Any

import numpy as np
import torch

from app.recommender.embed_catalog import load_clip_model, load_embeddings
from app.utils.logger import get_logger

logger = get_logger(__name__)

_TEXT_EMBEDDINGS: np.ndarray | None = None
_PRODUCT_INDEX: list[dict[str, Any]] | None = None
_MODEL = None
_PROCESSOR = None
_DEVICE = None


def _cosine_similarity_matrix(query_vec: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    """
    query_vec: shape (d,)
    matrix: shape (n, d)
    returns: shape (n,)
    """
    query_norm = np.linalg.norm(query_vec)
    matrix_norms = np.linalg.norm(matrix, axis=1)

    query_norm = max(query_norm, 1e-12)
    matrix_norms = np.clip(matrix_norms, 1e-12, None)

    sims = matrix @ query_vec / (matrix_norms * query_norm)
    return sims


def _ensure_loaded() -> None:
    global _TEXT_EMBEDDINGS, _PRODUCT_INDEX, _MODEL, _PROCESSOR, _DEVICE

    if _TEXT_EMBEDDINGS is None or _PRODUCT_INDEX is None:
        text_embeddings, product_index = load_embeddings()
        _TEXT_EMBEDDINGS = text_embeddings
        _PRODUCT_INDEX = product_index
        logger.info("Loaded text embeddings and product index into memory.")

    if _MODEL is None or _PROCESSOR is None or _DEVICE is None:
        _MODEL, _PROCESSOR, _DEVICE = load_clip_model()


def _encode_query_text(query_text: str) -> np.ndarray:
    _ensure_loaded()

    assert _MODEL is not None
    assert _PROCESSOR is not None
    assert _DEVICE is not None

    with torch.no_grad():
        inputs = _PROCESSOR(
            text=[query_text],
            padding=True,
            truncation=True,
            return_tensors="pt",
        )
        inputs = {k: v.to(_DEVICE) for k, v in inputs.items()}

        text_outputs = _MODEL.text_model(
            input_ids=inputs["input_ids"],
            attention_mask=inputs["attention_mask"],
        )
        pooled = text_outputs.pooler_output
        text_features = _MODEL.text_projection(pooled)
        text_features = torch.nn.functional.normalize(text_features, p=2, dim=-1)

        query_embedding = text_features[0].detach().cpu().numpy().astype("float32")

    return query_embedding


def search_by_text(query_text: str, top_n: int = 100) -> list[dict[str, Any]]:
    _ensure_loaded()

    assert _TEXT_EMBEDDINGS is not None
    assert _PRODUCT_INDEX is not None

    query_embedding = _encode_query_text(query_text)
    similarities = _cosine_similarity_matrix(query_embedding, _TEXT_EMBEDDINGS)

    top_indices = np.argsort(similarities)[::-1][:top_n]

    results: list[dict[str, Any]] = []
    for rank, idx in enumerate(top_indices, start=1):
        product = dict(_PRODUCT_INDEX[idx])
        retrieval_score = float(similarities[idx])

        results.append(
            {
                "rank": rank,
                "product": product,
                "retrieval_score": retrieval_score,
            }
        )

    return results


def search_by_image(image_bytes: bytes, top_n: int = 100) -> list[dict[str, Any]]:
    raise NotImplementedError(
        "Image retrieval is not implemented yet because only text embeddings are available."
    )


def search_hybrid(query_text: str, image_bytes: bytes, top_n: int = 100) -> list[dict[str, Any]]:
    raise NotImplementedError(
        "Hybrid retrieval is not implemented yet because only text embeddings are available."
    )