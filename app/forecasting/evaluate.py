from __future__ import annotations

import math
from typing import Any

import numpy as np


def mae(y_true, y_pred) -> float:
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    return float(np.mean(np.abs(y_true - y_pred)))


def rmse(y_true, y_pred) -> float:
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    return float(math.sqrt(np.mean((y_true - y_pred) ** 2)))


def wape(y_true, y_pred) -> float:
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    denom = np.sum(np.abs(y_true))
    if denom == 0:
        return 0.0
    return float(np.sum(np.abs(y_true - y_pred)) / denom)


def mape(y_true, y_pred) -> float:
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)
    mask = y_true != 0
    if not np.any(mask):
        return 0.0
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])))


def interval_coverage(y_true, lower, upper) -> float:
    y_true = np.array(y_true, dtype=float)
    lower = np.array(lower, dtype=float)
    upper = np.array(upper, dtype=float)
    covered = (y_true >= lower) & (y_true <= upper)
    return float(np.mean(covered))


def evaluate_forecast_model(
    y_true,
    point_pred,
    lower_pred,
    upper_pred,
) -> dict[str, float]:
    return {
        "mae": round(mae(y_true, point_pred), 4),
        "rmse": round(rmse(y_true, point_pred), 4),
        "wape": round(wape(y_true, point_pred), 4),
        "mape": round(mape(y_true, point_pred), 4),
        "interval_coverage": round(interval_coverage(y_true, lower_pred, upper_pred), 4),
    }