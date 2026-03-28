from __future__ import annotations

import re
from typing import Any

COLOR_MAP = {
    "navy": "blue",
    "sky blue": "blue",
    "light blue": "blue",
    "royal blue": "blue",
    "maroon": "red",
    "wine": "red",
    "cream": "white",
    "ivory": "white",
    "off white": "white",
    "charcoal": "gray",
    "grey": "gray",
    "mustard": "yellow",
    "olive": "green",
    "peach": "orange",
    "lavender": "purple",
    "beige": "brown",
    "tan": "brown",
}

CATEGORY_MAP = {
    "kurti": "kurta",
    "kurtis": "kurta",
    "tshirt": "t-shirt",
    "tee": "t-shirt",
    "tees": "t-shirt",
    "top": "tops",
    "tops": "tops",
    "dress": "dresses",
    "shirt": "shirts",
    "jean": "jeans",
    "trouser": "trousers",
    "hoodie": "hoodies",
    "sneaker": "sneakers",
}

KNOWN_CATEGORIES = {
    "kurta", "dresses", "shirts", "tops", "jeans", "trousers",
    "skirts", "jackets", "hoodies", "sarees", "t-shirts",
    "ethnic sets", "sneakers", "heels", "sandals", "bags"
}

KNOWN_OCCASIONS = {
    "casual", "festive", "party", "office", "wedding",
    "college", "vacation", "formal", "sports", "daily"
}

KNOWN_STYLES = {
    "ethnic", "fusion", "minimal", "boho", "elegant", "streetwear",
    "floral", "pastel", "vintage", "modern", "printed", "solid",
    "oversized", "chic", "traditional"
}

KNOWN_GENDERS = {"men", "women", "unisex", "boys", "girls"}


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().lower())


def normalize_color(value: str) -> str:
    if not value:
        return ""
    value = _clean_text(value)
    return COLOR_MAP.get(value, value)


def normalize_category(value: str) -> str:
    if not value:
        return ""
    value = _clean_text(value)
    return CATEGORY_MAP.get(value, value)


def build_metadata_text(product: dict[str, Any]) -> str:
    style_tags = product.get("style_tags", [])
    if isinstance(style_tags, list):
        style_text = ", ".join(style_tags)
    else:
        style_text = str(style_tags)

    parts = [
        product.get("name", ""),
        f"Category: {product.get('category', '')}",
        f"Sub-category: {product.get('sub_category', '')}",
        f"Description: {product.get('description', '')}",
        f"Color: {product.get('color', '')}",
        f"Color family: {product.get('color_family', '')}",
        f"Gender: {product.get('gender', '')}",
        f"Season: {product.get('season', '')}",
        f"Occasion: {product.get('occasion', '')}",
        f"Material: {product.get('material', '')}",
        f"Fit: {product.get('fit', '')}",
        f"Pattern: {product.get('pattern', '')}",
        f"Style tags: {style_text}",
        f"Price: {product.get('price', '')}",
    ]
    return ". ".join(part for part in parts if part).strip()


def extract_query_attributes(query: str) -> dict[str, Any]:
    text = _clean_text(query)

    category = None
    for cat in sorted(KNOWN_CATEGORIES, key=len, reverse=True):
        if cat in text:
            category = cat
            break

    occasion = None
    for occ in sorted(KNOWN_OCCASIONS, key=len, reverse=True):
        if occ in text:
            occasion = occ
            break

    colors = []
    for raw_color in set(list(COLOR_MAP.keys()) + list(COLOR_MAP.values())):
        if raw_color in text:
            colors.append(normalize_color(raw_color))
    colors = sorted(set(colors))

    style_tags = [style for style in KNOWN_STYLES if style in text]

    gender = None
    for g in KNOWN_GENDERS:
        if g in text:
            gender = g
            break

    price_intent = None
    if any(token in text for token in ["cheap", "budget", "affordable", "low price", "under"]):
        price_intent = "budget"
    elif any(token in text for token in ["premium", "luxury", "high-end", "designer"]):
        price_intent = "premium"
    else:
        price_intent = "mid"

    return {
        "category": category,
        "occasion": occasion,
        "colors": colors,
        "style_tags": style_tags,
        "gender": gender,
        "price_intent": price_intent,
        "raw_query": query,
    }