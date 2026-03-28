from __future__ import annotations

from typing import Any

from app.recommender.preprocess import extract_query_attributes
from app.recommender.retrieve import search_by_image, search_by_text, search_hybrid
from app.recommender.rerank import (
    build_explanation,
    category_match_score,
    color_match_score,
    compute_final_score,
    inventory_score,
    occasion_match_score,
    price_fit_score,
    style_match_score,
)
from app.utils.config import DEFAULT_TOP_K
from app.utils.helpers import compute_eta_from_distance


def _best_stock_row_for_product(
    product: dict[str, Any],
    inventory: list[dict[str, Any]],
    pincode: str | None = None,
) -> dict[str, Any] | None:
    sku_id = product.get("sku_id")
    rows = [row for row in inventory if row.get("sku_id") == sku_id]
    if not rows:
        return None

    if pincode:
        local = [row for row in rows if row.get("pincode") == pincode]
        if local:
            rows = local

    rows = sorted(rows, key=lambda x: int(x.get("available_stock", 0)), reverse=True)
    best = dict(rows[0])

    if "estimated_delivery_mins" not in best:
        distance = float(best.get("distance_km", 5.0))
        best["estimated_delivery_mins"] = compute_eta_from_distance(distance)

    return best


def _rerank_candidates(
    candidates: list[dict[str, Any]],
    request: Any,
    inventory: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    parsed_query = extract_query_attributes(getattr(request, "text_query", "") or "")

    reranked = []
    for item in candidates:
        product = item["product"]
        retrieval_score = float(item["retrieval_score"])

        cat_score = category_match_score(product, parsed_query)
        occ_score = occasion_match_score(product, parsed_query)
        clr_score = color_match_score(product, parsed_query)
        sty_score = style_match_score(product, parsed_query)
        stk_score = inventory_score(product, getattr(request, "pincode", None), inventory)
        prc_score = price_fit_score(product, request)

        popularity = float(product.get("popularity_score", 0.5))
        return_rate = float(product.get("return_rate", 0.0))

        final_score = compute_final_score(
            retrieval_score=retrieval_score,
            category_score=cat_score,
            occasion_score=occ_score,
            color_score=clr_score,
            style_score=sty_score,
            stock_score=stk_score,
            price_score=prc_score,
            popularity_score=popularity,
            return_rate=return_rate,
        )

        stock_row = _best_stock_row_for_product(product, inventory, getattr(request, "pincode", None))
        explanation = build_explanation(product, parsed_query, stock_row)

        reranked.append({
            **product,
            "retrieval_score": retrieval_score,
            "final_score": float(final_score),
            "matched_attributes": explanation["matched_attributes"],
            "warehouse_id": explanation["warehouse_id"],
            "available_stock": explanation["available_stock"],
            "estimated_delivery_mins": explanation["estimated_delivery_mins"],
        })

    reranked.sort(key=lambda x: x["final_score"], reverse=True)
    return reranked


def recommend_by_text(request: Any, catalogue: list[dict[str, Any]], inventory: list[dict[str, Any]]) -> dict[str, Any]:
    text_query = getattr(request, "text_query", None)
    if not text_query:
        return {"mode": "text", "results": []}

    candidates = search_by_text(text_query, top_n=100)
    ranked = _rerank_candidates(candidates, request, inventory)

    top_k = getattr(request, "top_k", DEFAULT_TOP_K) or DEFAULT_TOP_K
    results = ranked[:top_k]

    return {
        "mode": "text",
        "results": results,
        "count": len(results),
    }


def recommend_by_image(image_bytes: bytes, request: Any, catalogue: list[dict[str, Any]], inventory: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = search_by_image(image_bytes, top_n=100)
    ranked = _rerank_candidates(candidates, request, inventory)

    top_k = getattr(request, "top_k", DEFAULT_TOP_K) or DEFAULT_TOP_K
    results = ranked[:top_k]

    return {
        "mode": "image",
        "results": results,
        "count": len(results),
    }


def recommend_multimodal(request: Any, image_bytes: bytes, catalogue: list[dict[str, Any]], inventory: list[dict[str, Any]]) -> dict[str, Any]:
    text_query = getattr(request, "text_query", None) or ""
    candidates = search_hybrid(text_query, image_bytes, top_n=100)
    ranked = _rerank_candidates(candidates, request, inventory)

    top_k = getattr(request, "top_k", DEFAULT_TOP_K) or DEFAULT_TOP_K
    results = ranked[:top_k]

    return {
        "mode": "multimodal",
        "results": results,
        "count": len(results),
    }