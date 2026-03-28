from __future__ import annotations

import math
from datetime import date, datetime
from typing import Any


def sigmoid(x: float) -> float:
    x = max(min(x, 500), -500)
    return 1.0 / (1.0 + math.exp(-x))


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    if denominator == 0:
        return default
    return numerator / denominator


def normalize_scores(scores: list[float]) -> list[float]:
    if not scores:
        return []

    min_score = min(scores)
    max_score = max(scores)

    if math.isclose(min_score, max_score):
        return [1.0 for _ in scores]

    return [(score - min_score) / (max_score - min_score) for score in scores]


def compute_eta_from_distance(distance_km: float, base_minutes: int = 10, speed_kmph: float = 25.0) -> int:
    """
    Estimate ETA in minutes from distance.
    """
    travel_minutes = (distance_km / speed_kmph) * 60.0
    return max(1, int(round(base_minutes + travel_minutes)))


def serialize_datetime(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return value