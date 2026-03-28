from __future__ import annotations

import joblib
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder

from app.utils.config import (
    LOWER_QUANTILE_MODEL_FILE,
    POINT_FORECAST_MODEL_FILE,
    UPPER_QUANTILE_MODEL_FILE,
    ensure_directories,
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


def _get_feature_columns(df: pd.DataFrame) -> tuple[list[str], list[str]]:
    target_col = "units_sold"
    exclude = {"timestamp_hour", target_col, "name", "description", "metadata_text", "image_url"}
    feature_cols = [c for c in df.columns if c not in exclude]

    numeric_cols = [c for c in feature_cols if pd.api.types.is_numeric_dtype(df[c])]
    categorical_cols = [c for c in feature_cols if c not in numeric_cols]
    return numeric_cols, categorical_cols


def _build_preprocessor(numeric_cols: list[str], categorical_cols: list[str]) -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            ("num", Pipeline([
                ("imputer", SimpleImputer(strategy="constant", fill_value=0)),
            ]), numeric_cols),
            ("cat", Pipeline([
                ("imputer", SimpleImputer(strategy="constant", fill_value="unknown")),
                ("onehot", OneHotEncoder(handle_unknown="ignore")),
            ]), categorical_cols),
        ]
    )


def train_point_forecast_model(df: pd.DataFrame):
    numeric_cols, categorical_cols = _get_feature_columns(df)
    X = df[numeric_cols + categorical_cols]
    y = df["units_sold"].clip(lower=0)

    preprocessor = _build_preprocessor(numeric_cols, categorical_cols)
    model = GradientBoostingRegressor(
        loss="squared_error",
        n_estimators=200,
        learning_rate=0.05,
        max_depth=3,
        random_state=42,
    )

    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("model", model),
    ])
    pipeline.fit(X, y)
    logger.info("Trained point forecast model")
    return pipeline


def train_quantile_model(df: pd.DataFrame, quantile: float = 0.1):
    numeric_cols, categorical_cols = _get_feature_columns(df)
    X = df[numeric_cols + categorical_cols]
    y = df["units_sold"].clip(lower=0)

    preprocessor = _build_preprocessor(numeric_cols, categorical_cols)
    model = GradientBoostingRegressor(
        loss="quantile",
        alpha=quantile,
        n_estimators=200,
        learning_rate=0.05,
        max_depth=3,
        random_state=42,
    )

    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("model", model),
    ])
    pipeline.fit(X, y)
    logger.info("Trained quantile forecast model for quantile=%s", quantile)
    return pipeline


def save_models(point_model, lower_model, upper_model) -> None:
    ensure_directories()
    joblib.dump(point_model, POINT_FORECAST_MODEL_FILE)
    joblib.dump(lower_model, LOWER_QUANTILE_MODEL_FILE)
    joblib.dump(upper_model, UPPER_QUANTILE_MODEL_FILE)
    logger.info("Saved forecast models to disk")