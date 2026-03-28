from __future__ import annotations

from math import ceil
from typing import Any

from app.utils.config import INVENTORY_CONFIG


def calculate_transfer_quantity(projected_deficit: float, donor_item: dict[str, Any]) -> int:
    buffer_units = int(INVENTORY_CONFIG.get("default_transfer_buffer_units", 3))

    available_stock = float(donor_item.get("available_stock", 0))
    safety_stock = float(donor_item.get("safety_stock", 0))

    donor_transferable = max(0.0, available_stock - safety_stock)
    required_units = max(0.0, projected_deficit + buffer_units)

    qty = min(required_units, donor_transferable)
    return max(0, int(ceil(qty)))


def create_transfer_plan(
    sku_id: str,
    recipient_item: dict[str, Any],
    donor_item: dict[str, Any],
    projected_deficit: float,
    stockout_risk_before: float,
    sla_risk_before: float,
) -> dict[str, Any]:
    transfer_qty = calculate_transfer_quantity(projected_deficit, donor_item)

    risk_after = max(0.0, stockout_risk_before - min(0.75, transfer_qty / max(projected_deficit + 1.0, 1.0)))
    sla_after = max(0.0, sla_risk_before - 0.40)

    transfer_cost = round(transfer_qty * float(donor_item.get("transfer_cost_per_unit", 0)), 2)

    return {
        "action": "transfer",
        "sku_id": sku_id,
        "product_id": recipient_item.get("product_id"),
        "recipient_warehouse": recipient_item.get("warehouse_id"),
        "recipient_pincode": recipient_item.get("pincode"),
        "donor_warehouse": donor_item.get("warehouse_id"),
        "transfer_qty": transfer_qty,
        "distance_km": round(float(donor_item.get("distance_km", 0)), 2),
        "estimated_transfer_mins": int(round(float(donor_item.get("estimated_transfer_mins", 0)))),
        "transfer_cost": transfer_cost,
        "stockout_risk_before": stockout_risk_before,
        "stockout_risk_after": round(risk_after, 4),
        "sla_risk_before": sla_risk_before,
        "sla_risk_after": round(sla_after, 4),
        "sla_improvement_pct": round(max(0.0, (sla_risk_before - sla_after) * 100), 2),
        "decision_score": donor_item.get("donor_score", 0.0),
        "status": "proposed",
    }


def fallback_reorder_plan(
    sku_id: str,
    recipient_item: dict[str, Any],
    projected_deficit: float,
    stockout_risk_before: float,
    sla_risk_before: float,
) -> dict[str, Any]:
    reorder_qty = max(
        int(ceil(projected_deficit + INVENTORY_CONFIG.get("default_transfer_buffer_units", 3))),
        int(recipient_item.get("reorder_threshold", 5)),
    )

    return {
        "action": "reorder",
        "sku_id": sku_id,
        "product_id": recipient_item.get("product_id"),
        "recipient_warehouse": recipient_item.get("warehouse_id"),
        "recipient_pincode": recipient_item.get("pincode"),
        "donor_warehouse": None,
        "transfer_qty": reorder_qty,
        "distance_km": None,
        "estimated_transfer_mins": None,
        "transfer_cost": None,
        "stockout_risk_before": stockout_risk_before,
        "stockout_risk_after": round(max(0.0, stockout_risk_before - 0.30), 4),
        "sla_risk_before": sla_risk_before,
        "sla_risk_after": round(max(0.0, sla_risk_before - 0.20), 4),
        "sla_improvement_pct": round(min(100.0, sla_risk_before * 20), 2),
        "decision_score": 0.0,
        "status": "proposed",
    }