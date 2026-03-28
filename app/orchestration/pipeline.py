from __future__ import annotations

from typing import Any

from app.forecasting.predict import predict_forecast
from app.orchestration.donor_selector import get_candidate_donors, rank_donors
from app.orchestration.explain import explain_reorder_action, explain_transfer_action, summarize_run
from app.orchestration.optimizer import create_transfer_plan, fallback_reorder_plan
from app.orchestration.risk_engine import (
    compute_projected_deficit,
    compute_sla_risk,
    compute_stockout_risk,
    risk_label,
)


def _estimate_urgency(stockout_risk: float, sla_risk: float) -> str:
    combined = max(stockout_risk, sla_risk)
    if combined >= 0.85:
        return "critical"
    if combined >= 0.65:
        return "high"
    if combined >= 0.35:
        return "medium"
    return "low"


def _pick_recipient_items(
    inventory: list[dict[str, Any]],
    pincode: str | None = None,
    sku_id: str | None = None,
) -> list[dict[str, Any]]:
    rows = inventory
    if pincode:
        rows = [r for r in rows if r.get("pincode") == pincode]
    if sku_id:
        rows = [r for r in rows if r.get("sku_id") == sku_id]
    return rows


def get_inventory_snapshot(
    warehouse_id: str,
    inventory: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [row for row in inventory if row.get("warehouse_id") == warehouse_id]


def get_risk_summary(
    inventory: list[dict[str, Any]],
    demand_history: list[dict[str, Any]],
    pincode: str | None = None,
    sku_id: str | None = None,
) -> list[dict[str, Any]]:
    recipients = _pick_recipient_items(inventory, pincode=pincode, sku_id=sku_id)
    risks = []

    for item in recipients:
        try:
            forecast = predict_forecast(
                sku_id=item["sku_id"],
                pincode=item["pincode"],
                horizon_hours=6,
                demand_history=demand_history,
            )
        except Exception:
            continue

        forecast_rows = forecast.get("forecast", [])
        if not forecast_rows:
            continue

        total_upper = sum(float(x.get("upper_bound", 0)) for x in forecast_rows)
        total_pred = sum(float(x.get("predicted_demand", 0)) for x in forecast_rows)

        available_stock = float(item.get("available_stock", 0))
        safety_stock = float(item.get("safety_stock", 0))

        projected_deficit = compute_projected_deficit(
            available_stock=available_stock,
            upper_forecast=total_upper,
            safety_stock=safety_stock,
        )
        stockout_risk = compute_stockout_risk(projected_deficit, safety_stock)
        sla_risk = compute_sla_risk(
            eta_minutes=30,
            urgency="medium",
            predicted_demand=total_pred,
        )

        risks.append({
            "warehouse_id": item.get("warehouse_id"),
            "pincode": item.get("pincode"),
            "sku_id": item.get("sku_id"),
            "product_id": item.get("product_id"),
            "available_stock": available_stock,
            "projected_deficit": projected_deficit,
            "stockout_risk": stockout_risk,
            "sla_risk": sla_risk,
            "risk_label": risk_label(max(stockout_risk, sla_risk)),
        })

    return risks


def run_orchestration(
    inventory: list[dict[str, Any]],
    transfer_matrix: list[dict[str, Any]],
    demand_history: list[dict[str, Any]],
    pincode: str | None = None,
    sku_id: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    recipient_items = _pick_recipient_items(inventory, pincode=pincode, sku_id=sku_id)

    actions = []
    risks = []

    for item in recipient_items:
        try:
            forecast_result = predict_forecast(
                sku_id=item["sku_id"],
                pincode=item["pincode"],
                horizon_hours=6,
                demand_history=demand_history,
            )
        except Exception:
            continue

        forecast_rows = forecast_result.get("forecast", [])
        if not forecast_rows:
            continue

        total_predicted = sum(float(r.get("predicted_demand", 0)) for r in forecast_rows)
        total_upper = sum(float(r.get("upper_bound", 0)) for r in forecast_rows)

        available_stock = float(item.get("available_stock", 0))
        safety_stock = float(item.get("safety_stock", 0))

        projected_deficit = compute_projected_deficit(
            available_stock=available_stock,
            upper_forecast=total_upper,
            safety_stock=safety_stock,
        )

        stockout_risk = compute_stockout_risk(projected_deficit, safety_stock)
        urgency = _estimate_urgency(stockout_risk, 0.5)
        sla_risk = compute_sla_risk(
            eta_minutes=30,
            urgency=urgency,
            predicted_demand=total_predicted,
        )

        risk_info = {
            "warehouse_id": item.get("warehouse_id"),
            "pincode": item.get("pincode"),
            "sku_id": item.get("sku_id"),
            "product_id": item.get("product_id"),
            "available_stock": available_stock,
            "projected_deficit": projected_deficit,
            "stockout_risk": stockout_risk,
            "sla_risk": sla_risk,
            "risk_label": risk_label(max(stockout_risk, sla_risk)),
        }
        risks.append(risk_info)

        if projected_deficit <= 0:
            continue

        candidates = get_candidate_donors(
            sku_id=item["sku_id"],
            recipient_warehouse=item["warehouse_id"],
            inventory=inventory,
            transfer_matrix=transfer_matrix,
        )
        ranked_donors = rank_donors(
            candidates=candidates,
            projected_deficit=projected_deficit,
            recipient_warehouse=item["warehouse_id"],
        )

        if ranked_donors:
            best_donor = ranked_donors[0]
            action = create_transfer_plan(
                sku_id=item["sku_id"],
                recipient_item=item,
                donor_item=best_donor,
                projected_deficit=projected_deficit,
                stockout_risk_before=stockout_risk,
                sla_risk_before=sla_risk,
            )
            action["explanation"] = explain_transfer_action(action)
        else:
            action = fallback_reorder_plan(
                sku_id=item["sku_id"],
                recipient_item=item,
                projected_deficit=projected_deficit,
                stockout_risk_before=stockout_risk,
                sla_risk_before=sla_risk,
            )
            action["explanation"] = explain_reorder_action(action)

        if not dry_run:
            action["status"] = "recommended"

        actions.append(action)

    return {
        "actions": actions,
        "risks": risks,
        "summary": summarize_run(actions, risks),
    }