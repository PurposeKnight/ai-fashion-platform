from __future__ import annotations

from datetime import timedelta
from typing import Any

import joblib
import pandas as pd

from app.forecasting.feature_engineering import prepare_training_matrix
from app.forecasting.preprocess import prepare_base_dataframe
from app.utils.config import (
    FORECAST_HORIZON_HOURS,
    LOWER_QUANTILE_MODEL_FILE,
    POINT_FORECAST_MODEL_FILE,
    RISK_THRESHOLDS,
    UPPER_QUANTILE_MODEL_FILE,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


def load_models():
    point_model = joblib.load(POINT_FORECAST_MODEL_FILE)
    lower_model = joblib.load(LOWER_QUANTILE_MODEL_FILE)
    upper_model = joblib.load(UPPER_QUANTILE_MODEL_FILE)
    return point_model, lower_model, upper_model


def derive_risk_level(predicted: float, upper: float, stock: float) -> str:
    if stock <= 0:
        return "high"
    coverage_ratio = upper / max(stock, 1)
    if coverage_ratio >= RISK_THRESHOLDS["medium"]:
        return "high"
    if coverage_ratio >= RISK_THRESHOLDS["low"]:
        return "medium"
    return "low"


def extract_top_drivers(row: dict[str, Any]) -> list[str]:
    drivers = []

    if row.get("event_flag", 0) == 1:
        drivers.append("local event")
    if row.get("promo_flag", 0) == 1:
        drivers.append("promotion active")
    if row.get("weekend_flag", 0) == 1:
        drivers.append("weekend uplift")
    if row.get("rain_flag", 0) == 1:
        drivers.append("rain impact")
    if row.get("hour", row.get("hour_of_day", 0)) in [18, 19, 20, 21]:
        drivers.append("evening peak")
    if row.get("rolling_mean_24h", 0) > row.get("rolling_mean_6h", 0):
        drivers.append("stable demand trend")
    if row.get("lag_1", 0) > row.get("rolling_mean_6h", 0):
        drivers.append("recent demand spike")

    return drivers[:3] if drivers else ["historical demand pattern"]


def build_future_features(
    sku_id: str,
    pincode: str,
    horizon_hours: int,
    demand_history: list[dict[str, Any]],
) -> pd.DataFrame:
    base_df = prepare_base_dataframe(demand_history)
    base_df = base_df[(base_df["sku_id"] == sku_id) & (base_df["pincode"] == pincode)].copy()

    if base_df.empty:
        raise ValueError(f"No demand history found for sku_id={sku_id}, pincode={pincode}")

    base_df = prepare_training_matrix(base_df)

    last_row = base_df.sort_values("timestamp_hour").iloc[-1].copy()
    last_ts = pd.to_datetime(last_row["timestamp_hour"])

    future_rows = []
    history_df = base_df.copy()

    for step in range(1, horizon_hours + 1):
        future_ts = last_ts + timedelta(hours=step)
        row = last_row.copy()

        row["timestamp_hour"] = future_ts
        row["hour"] = future_ts.hour
        row["hour_of_day"] = future_ts.hour
        row["day"] = future_ts.day
        row["day_of_week"] = future_ts.dayofweek
        row["weekend_flag"] = 1 if future_ts.dayofweek >= 5 else 0
        row["month"] = future_ts.month

        # propagate recent state, simple baseline for future flags
        row["promo_flag"] = int(last_row.get("promo_flag", 0))
        row["event_flag"] = int(last_row.get("event_flag", 0))
        row["rain_flag"] = int(last_row.get("rain_flag", 0))
        row["temperature"] = float(last_row.get("temperature", 25))
        row["precipitation"] = float(last_row.get("precipitation", 0))
        row["stock_available"] = float(last_row.get("stock_available", 20))
        row["page_views"] = float(last_row.get("page_views", 10))
        row["add_to_cart_count"] = float(last_row.get("add_to_cart_count", 2))
        row["returns_count"] = float(last_row.get("returns_count", 0))

        # rolling lag approximation from existing history
        hist = history_df["units_sold"].tolist()
        row["lag_1"] = hist[-1] if len(hist) >= 1 else 0
        row["lag_2"] = hist[-2] if len(hist) >= 2 else row["lag_1"]
        row["lag_6"] = hist[-6] if len(hist) >= 6 else row["lag_1"]
        row["lag_24"] = hist[-24] if len(hist) >= 24 else row["lag_1"]
        row["lag_168"] = hist[-168] if len(hist) >= 168 else row["lag_1"]

        recent_3 = hist[-3:] if len(hist) >= 3 else hist
        recent_6 = hist[-6:] if len(hist) >= 6 else hist
        recent_24 = hist[-24:] if len(hist) >= 24 else hist

        row["rolling_mean_3h"] = float(pd.Series(recent_3).mean()) if recent_3 else 0
        row["rolling_mean_6h"] = float(pd.Series(recent_6).mean()) if recent_6 else 0
        row["rolling_mean_24h"] = float(pd.Series(recent_24).mean()) if recent_24 else 0
        row["rolling_std_6h"] = float(pd.Series(recent_6).std()) if len(recent_6) > 1 else 0
        row["rolling_std_24h"] = float(pd.Series(recent_24).std()) if len(recent_24) > 1 else 0

        future_rows.append(row.to_dict())

        # placeholder append so next horizon can reference previous row
        placeholder = row.copy()
        placeholder["units_sold"] = row["lag_1"]
        history_df = pd.concat([history_df, pd.DataFrame([placeholder])], ignore_index=True)

    future_df = pd.DataFrame(future_rows)
    return future_df


def predict_forecast(
    sku_id: str,
    pincode: str,
    horizon_hours: int = FORECAST_HORIZON_HOURS,
    demand_history: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if demand_history is None:
        raise ValueError("demand_history is required for prediction")

    point_model, lower_model, upper_model = load_models()
    future_df = build_future_features(sku_id, pincode, horizon_hours, demand_history)

    X = future_df.drop(columns=["units_sold"], errors="ignore")

    point_pred = point_model.predict(X)
    lower_pred = lower_model.predict(X)
    upper_pred = upper_model.predict(X)

    results = []
    for idx, row in future_df.iterrows():
        predicted = max(0.0, float(point_pred[idx]))
        lower = max(0.0, float(lower_pred[idx]))
        upper = max(predicted, float(upper_pred[idx]))
        stock = float(row.get("stock_available", 0))

        results.append({
            "timestamp_hour": pd.to_datetime(row["timestamp_hour"]).isoformat(),
            "predicted_demand": round(predicted, 2),
            "lower_bound": round(lower, 2),
            "upper_bound": round(upper, 2),
            "risk_level": derive_risk_level(predicted, upper, stock),
            "top_drivers": extract_top_drivers(row.to_dict()),
        })

    logger.info("Generated forecast for sku_id=%s, pincode=%s", sku_id, pincode)
    return {
        "sku_id": sku_id,
        "pincode": pincode,
        "horizon_hours": horizon_hours,
        "forecast": results,
    }