from __future__ import annotations

import os
import pickle
from typing import Any

import numpy as np
import torch
from transformers import CLIPModel, CLIPProcessor

from app.utils.logger import get_logger

logger = get_logger(__name__)

MODEL_NAME = "openai/clip-vit-base-patch32"
EMBEDDINGS_DIR = "app/artifacts/embeddings"


def load_clip_model():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = CLIPModel.from_pretrained(MODEL_NAME)
    processor = CLIPProcessor.from_pretrained(MODEL_NAME)
    model.to(device)
    model.eval()
    logger.info("Loaded CLIP model on device: %s", device)
    return model, processor, device


def embed_catalog_text(
    catalogue: list[dict[str, Any]],
    batch_size: int = 32,
) -> tuple[np.ndarray, list[dict[str, Any]]]:
    model, processor, device = load_clip_model()

    texts = [item["metadata_text"] for item in catalogue]
    all_embeddings: list[np.ndarray] = []
    product_index: list[dict[str, Any]] = []

    with torch.no_grad():
        for start in range(0, len(texts), batch_size):
            batch_texts = texts[start : start + batch_size]

            inputs = processor(
                text=batch_texts,
                padding=True,
                truncation=True,
                return_tensors="pt",
            )
            inputs = {k: v.to(device) for k, v in inputs.items()}

            text_outputs = model.text_model(
                input_ids=inputs["input_ids"],
                attention_mask=inputs["attention_mask"],
            )

            pooled = text_outputs.pooler_output
            text_features = model.text_projection(pooled)
            text_features = torch.nn.functional.normalize(text_features, p=2, dim=-1)

            all_embeddings.append(
                text_features.detach().cpu().numpy().astype("float32")
            )

    embeddings = np.vstack(all_embeddings)

    for item in catalogue:
        product_index.append(
            {
                "product_id": item["product_id"],
                "sku_id": item["sku_id"],
                "name": item["name"],
                "category": item["category"],
                "sub_category": item["sub_category"],
                "price": item["price"],
                "metadata_text": item["metadata_text"],
                "image_url": item["image_url"],
            }
        )

    return embeddings, product_index


def save_embeddings(
    text_embeddings: np.ndarray,
    product_index: list[dict[str, Any]],
    embeddings_filename: str = "catalog_text_embeddings.npy",
    index_filename: str = "product_index.pkl",
) -> None:
    os.makedirs(EMBEDDINGS_DIR, exist_ok=True)

    np.save(os.path.join(EMBEDDINGS_DIR, embeddings_filename), text_embeddings)

    with open(os.path.join(EMBEDDINGS_DIR, index_filename), "wb") as f:
        pickle.dump(product_index, f)

    logger.info("Saved embeddings and product index.")


def load_embeddings(
    embeddings_filename: str = "catalog_text_embeddings.npy",
    index_filename: str = "product_index.pkl",
) -> tuple[np.ndarray, list[dict[str, Any]]]:
    text_embeddings = np.load(os.path.join(EMBEDDINGS_DIR, embeddings_filename))

    with open(os.path.join(EMBEDDINGS_DIR, index_filename), "rb") as f:
        product_index = pickle.load(f)

    return text_embeddings, product_index