from __future__ import annotations

from typing import Any

from app.utils.helpers import safe_divide


def get_candidate_donors(
    sku_id: str,
    recipient_warehouse: str,
    inventory: list[dict[str, Any]],
    transfer_matrix: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    transfer_lookup = {
        (row["from_warehouse"], row["to_warehouse"]): row
        for row in transfer_matrix
    }

    candidates = []
    for item in inventory:
        if item.get("sku_id") != sku_id:
            continue
        if item.get("warehouse_id") == recipient_warehouse:
            continue

        available_stock = float(item.get("available_stock", 0))
        safety_stock = float(item.get("safety_stock", 0))
        surplus_stock = max(0.0, available_stock - safety_stock)

        if surplus_stock <= 0:
            continue

        route = transfer_lookup.get((item.get("warehouse_id"), recipient_warehouse))
        if not route:
            continue

        candidate = {
            **item,
            "surplus_stock": round(surplus_stock, 2),
            "distance_km": float(route.get("distance_km", 0)),
            "estimated_transfer_mins": float(route.get("estimated_transfer_mins", 999)),
            "transfer_cost_per_unit": float(route.get("transfer_cost_per_unit", 0)),
        }
        candidates.append(candidate)

    return candidates


def score_donor(
    candidate: dict[str, Any],
    projected_deficit: float,
    recipient_warehouse: str | None = None,
) -> float:
    surplus_stock = float(candidate.get("surplus_stock", 0))
    eta = float(candidate.get("estimated_transfer_mins", 999))
    distance = float(candidate.get("distance_km", 999))
    transfer_cost = float(candidate.get("transfer_cost_per_unit", 0))
    available_stock = float(candidate.get("available_stock", 0))
    safety_stock = float(candidate.get("safety_stock", 0))

    donor_post_transfer_safety = max(0.0, available_stock - projected_deficit - safety_stock)

    surplus_score = min(surplus_stock / max(projected_deficit, 1.0), 1.5)
    eta_score = 1.0 - min(eta / 120.0, 1.0)
    distance_score = 1.0 - min(distance / 50.0, 1.0)
    cost_score = 1.0 - min(transfer_cost / 25.0, 1.0)
    post_transfer_score = min(donor_post_transfer_safety / max(safety_stock, 1.0), 1.0)

    final = (
        0.35 * surplus_score
        + 0.20 * eta_score
        + 0.15 * distance_score
        + 0.15 * post_transfer_score
        + 0.15 * cost_score
    )
    return round(final, 4)


def rank_donors(
    candidates: list[dict[str, Any]],
    projected_deficit: float,
    recipient_warehouse: str | None = None,
) -> list[dict[str, Any]]:
    ranked = []
    for candidate in candidates:
        score = score_donor(candidate, projected_deficit, recipient_warehouse)
        ranked.append({
            **candidate,
            "donor_score": score,
        })

    ranked.sort(key=lambda x: x["donor_score"], reverse=True)
    return ranked