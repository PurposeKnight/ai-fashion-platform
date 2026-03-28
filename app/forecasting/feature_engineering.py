from __future__ import annotations

import pandas as pd

from app.utils.logger import get_logger

logger = get_logger(__name__)


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["timestamp_hour"] = pd.to_datetime(df["timestamp_hour"])

    df["hour"] = df["timestamp_hour"].dt.hour
    df["day"] = df["timestamp_hour"].dt.day
    df["day_of_week"] = df["timestamp_hour"].dt.dayofweek
    df["weekend_flag"] = (df["day_of_week"] >= 5).astype(int)
    df["month"] = df["timestamp_hour"].dt.month

    return df


def add_lag_features(df: pd.DataFrame, group_cols: list[str] = ["sku_id", "pincode"]) -> pd.DataFrame:
    df = df.copy().sort_values(group_cols + ["timestamp_hour"])

    lag_steps = [1, 2, 6, 24, 168]
    for lag in lag_steps:
        df[f"lag_{lag}"] = df.groupby(group_cols)["units_sold"].shift(lag)

    return df


def add_rolling_features(df: pd.DataFrame, group_cols: list[str] = ["sku_id", "pincode"]) -> pd.DataFrame:
    df = df.copy().sort_values(group_cols + ["timestamp_hour"])

    grp = df.groupby(group_cols)["units_sold"]

    df["rolling_mean_3h"] = grp.transform(lambda s: s.shift(1).rolling(3, min_periods=1).mean())
    df["rolling_mean_6h"] = grp.transform(lambda s: s.shift(1).rolling(6, min_periods=1).mean())
    df["rolling_mean_24h"] = grp.transform(lambda s: s.shift(1).rolling(24, min_periods=1).mean())

    df["rolling_std_6h"] = grp.transform(lambda s: s.shift(1).rolling(6, min_periods=2).std())
    df["rolling_std_24h"] = grp.transform(lambda s: s.shift(1).rolling(24, min_periods=2).std())

    return df


def add_weather_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "precipitation" in df.columns:
        df["rain_flag"] = (df["precipitation"] > 0).astype(int)

    if "temperature" in df.columns:
        df["is_hot"] = (df["temperature"] >= 30).astype(int)
        df["is_cold"] = (df["temperature"] <= 18).astype(int)

    return df


def add_event_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for col in ["event_flag", "promo_flag", "stockout_flag"]:
        if col in df.columns:
            df[col] = df[col].astype(int)
        else:
            df[col] = 0

    return df


def prepare_training_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Final feature table for model training.
    """
    df = df.copy()
    df = add_time_features(df)
    df = add_lag_features(df)
    df = add_rolling_features(df)
    df = add_weather_features(df)
    df = add_event_features(df)

    numeric_fill_zero = [
        "lag_1", "lag_2", "lag_6", "lag_24", "lag_168",
        "rolling_mean_3h", "rolling_mean_6h", "rolling_mean_24h",
        "rolling_std_6h", "rolling_std_24h",
        "temperature", "precipitation",
        "page_views", "add_to_cart_count",
        "stock_available", "returns_count",
    ]
    for col in numeric_fill_zero:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    categorical_fill_unknown = [
        "sku_id", "product_id", "category", "sub_category", "pincode",
        "warehouse_id", "occasion", "material", "fit", "pattern",
        "gender", "season", "color", "color_family",
    ]
    for col in categorical_fill_unknown:
        if col in df.columns:
            df[col] = df[col].fillna("unknown").astype(str)

    logger.info("Prepared training matrix with shape %s", df.shape)
    return df