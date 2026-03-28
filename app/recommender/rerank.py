from __future__ import annotations

from typing import Any

from app.recommender.preprocess import extract_query_attributes, normalize_color
from app.utils.config import INVENTORY_CONFIG, RECOMMENDER_WEIGHTS
from app.utils.helpers import safe_divide


def category_match_score(product: dict[str, Any], parsed_query: dict[str, Any]) -> float:
    query_cat = parsed_query.get("category")
    if not query_cat:
        return 0.5
    product_cat = str(product.get("category", "")).lower()
    product_sub = str(product.get("sub_category", "")).lower()
    if query_cat == product_cat:
        return 1.0
    if query_cat == product_sub:
        return 0.9
    return 0.0


def occasion_match_score(product: dict[str, Any], parsed_query: dict[str, Any]) -> float:
    query_occ = parsed_query.get("occasion")
    if not query_occ:
        return 0.5
    product_occ = str(product.get("occasion", "")).lower()
    return 1.0 if query_occ == product_occ else 0.0


def color_match_score(product: dict[str, Any], parsed_query: dict[str, Any]) -> float:
    query_colors = parsed_query.get("colors", [])
    if not query_colors:
        return 0.5

    product_color = normalize_color(str(product.get("color", "")).lower())
    product_family = str(product.get("color_family", "")).lower()

    if product_color in query_colors:
        return 1.0
    if product_family in query_colors:
        return 0.75
    return 0.0


def style_match_score(product: dict[str, Any], parsed_query: dict[str, Any]) -> float:
    query_styles = set(parsed_query.get("style_tags", []))
    if not query_styles:
        return 0.5

    product_styles = product.get("style_tags", [])
    if not isinstance(product_styles, list):
        product_styles = [str(product_styles)]
    product_styles = set(str(x).lower() for x in product_styles)

    overlap = len(query_styles & product_styles)
    return safe_divide(overlap, max(len(query_styles), 1), default=0.0)


def inventory_score(product: dict[str, Any], pincode: str | None, inventory: list[dict[str, Any]]) -> float:
    sku_id = product.get("sku_id")
    matches = [row for row in inventory if row.get("sku_id") == sku_id]

    if not matches:
        return 0.0

    local_matches = [row for row in matches if pincode and row.get("pincode") == pincode]
    target_rows = local_matches if local_matches else matches

    best_available = max(int(row.get("available_stock", 0)) for row in target_rows)
    if best_available <= 0:
        return 0.0
    if best_available >= 20:
        return 1.0
    return min(best_available / 20.0, 1.0)


def price_fit_score(product: dict[str, Any], request: Any) -> float:
    price = float(product.get("price", 0))

    price_min = getattr(request, "price_min", None)
    price_max = getattr(request, "price_max", None)

    if price_min is not None and price < price_min:
        return 0.0
    if price_max is not None and price > price_max:
        return 0.0

    price_intent = getattr(request, "price_intent", None)
    if price_intent == "budget":
        return 1.0 if price <= 1200 else 0.4
    if price_intent == "premium":
        return 1.0 if price >= 2500 else 0.4

    return 0.8


def compute_final_score(
    retrieval_score: float,
    category_score: float,
    occasion_score: float,
    color_score: float,
    style_score: float,
    stock_score: float,
    price_score: float,
    popularity_score: float,
    return_rate: float,
) -> float:
    w = RECOMMENDER_WEIGHTS
    return (
        w["retrieval_score"] * retrieval_score
        + w["category_match"] * category_score
        + w["occasion_match"] * occasion_score
        + w["color_match"] * color_score
        + w["style_match"] * style_score
        + w["inventory_score"] * stock_score
        + w["price_fit_score"] * price_score
        + w["popularity_score"] * popularity_score
        - w["return_rate_penalty"] * return_rate
    )


def build_explanation(product: dict[str, Any], parsed_query: dict[str, Any], stock_row: dict[str, Any] | None) -> dict[str, Any]:
    matched_attributes = []

    if parsed_query.get("category") and parsed_query["category"] in str(product.get("category", "")).lower():
        matched_attributes.append(parsed_query["category"])

    if parsed_query.get("occasion") and parsed_query["occasion"] == str(product.get("occasion", "")).lower():
        matched_attributes.append(parsed_query["occasion"])

    query_colors = parsed_query.get("colors", [])
    product_color = normalize_color(str(product.get("color", "")).lower())
    if product_color in query_colors:
        matched_attributes.append(product_color)

    product_styles = product.get("style_tags", [])
    if not isinstance(product_styles, list):
        product_styles = [str(product_styles)]
    for style in parsed_query.get("style_tags", []):
        if style in [s.lower() for s in product_styles]:
            matched_attributes.append(style)

    matched_attributes = list(dict.fromkeys(matched_attributes))

    return {
        "matched_attributes": matched_attributes,
        "warehouse_id": stock_row.get("warehouse_id") if stock_row else None,
        "available_stock": stock_row.get("available_stock") if stock_row else 0,
        "estimated_delivery_mins": stock_row.get("estimated_delivery_mins") if stock_row else None,
    }