from __future__ import annotations

from app.utils.config import RISK_THRESHOLDS
from app.utils.helpers import sigmoid


def compute_projected_deficit(
    available_stock: float,
    upper_forecast: float,
    safety_stock: float,
) -> float:
    required_stock = max(0.0, upper_forecast) + max(0.0, safety_stock)
    deficit = required_stock - max(0.0, available_stock)
    return round(max(0.0, deficit), 2)


def compute_stockout_risk(projected_deficit: float, safety_stock: float) -> float:
    if projected_deficit <= 0:
        return 0.0

    scale = max(float(safety_stock), 1.0)
    raw = projected_deficit / scale
    risk = sigmoid(raw)
    return round(min(max(risk, 0.0), 1.0), 4)


def compute_sla_risk(eta_minutes: float, urgency: str, predicted_demand: float) -> float:
    eta_minutes = max(0.0, float(eta_minutes))
    predicted_demand = max(0.0, float(predicted_demand))

    urgency_weight = {
        "low": 0.25,
        "medium": 0.50,
        "high": 0.80,
        "critical": 1.00,
    }.get(str(urgency).lower(), 0.50)

    eta_component = min(eta_minutes / 60.0, 1.5)
    demand_component = min(predicted_demand / 25.0, 1.0)

    raw_score = 0.55 * eta_component + 0.30 * urgency_weight + 0.15 * demand_component
    return round(min(max(raw_score, 0.0), 1.0), 4)


def risk_label(score: float) -> str:
    score = float(score)
    if score < RISK_THRESHOLDS["low"]:
        return "low"
    if score < RISK_THRESHOLDS["medium"]:
        return "medium"
    return "high"