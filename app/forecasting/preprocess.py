from __future__ import annotations

from typing import Any

import pandas as pd

from app.utils.config import DEMAND_HISTORY_FILE
from app.utils.logger import get_logger

logger = get_logger(__name__)


def load_demand_data() -> list[dict[str, Any]]:
    """
    Load demand history from processed JSON file.
    """
    if not DEMAND_HISTORY_FILE.exists():
        raise FileNotFoundError(f"Demand history file not found: {DEMAND_HISTORY_FILE}")

    df = pd.read_json(DEMAND_HISTORY_FILE)
    logger.info("Loaded demand data with %s rows", len(df))
    return df.to_dict(orient="records")


def prepare_base_dataframe(demand_history: list[dict[str, Any]]) -> pd.DataFrame:
    """
    Convert demand history records to a cleaned base dataframe.
    """
    df = pd.DataFrame(demand_history).copy()
    if df.empty:
        return df

    if "timestamp_hour" in df.columns:
        df["timestamp_hour"] = pd.to_datetime(df["timestamp_hour"])

    numeric_cols = [
        "units_sold",
        "stock_available",
        "returns_count",
        "page_views",
        "add_to_cart_count",
        "temperature",
        "precipitation",
        "hour_of_day",
        "day_of_week",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    bool_cols = ["stockout_flag", "promo_flag", "event_flag", "rain_flag", "weekend_flag"]
    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].astype(int)

    df = df.sort_values(["sku_id", "pincode", "timestamp_hour"]).reset_index(drop=True)
    logger.info("Prepared base dataframe with shape %s", df.shape)
    return df


def merge_product_context(df: pd.DataFrame, catalogue: list[dict[str, Any]]) -> pd.DataFrame:
    """
    Merge product metadata into demand dataframe.
    """
    if df.empty:
        return df

    catalogue_df = pd.DataFrame(catalogue).copy()
    keep_cols = [
        "product_id",
        "sku_id",
        "name",
        "category",
        "sub_category",
        "color",
        "color_family",
        "gender",
        "season",
        "occasion",
        "material",
        "fit",
        "pattern",
        "price",
        "popularity_score",
        "return_rate",
    ]
    keep_cols = [c for c in keep_cols if c in catalogue_df.columns]
    catalogue_df = catalogue_df[keep_cols].drop_duplicates(subset=["sku_id"])

    merged = df.merge(catalogue_df, on=["sku_id", "product_id"], how="left", suffixes=("", "_product"))
    logger.info("Merged product context; new shape %s", merged.shape)
    return merged


def merge_inventory_context(df: pd.DataFrame, inventory: list[dict[str, Any]]) -> pd.DataFrame:
    """
    Merge inventory fields into demand dataframe.
    """
    if df.empty:
        return df

    inv_df = pd.DataFrame(inventory).copy()
    keep_cols = [
        "warehouse_id",
        "sku_id",
        "pincode",
        "available_stock",
        "current_stock",
        "reserved_stock",
        "incoming_stock",
        "reorder_threshold",
        "safety_stock",
        "max_capacity",
    ]
    keep_cols = [c for c in keep_cols if c in inv_df.columns]
    inv_df = inv_df[keep_cols].drop_duplicates(subset=["warehouse_id", "sku_id", "pincode"])

    merged = df.merge(
        inv_df,
        on=["warehouse_id", "sku_id", "pincode"],
        how="left",
        suffixes=("", "_inventory"),
    )
    logger.info("Merged inventory context; new shape %s", merged.shape)
    return merged