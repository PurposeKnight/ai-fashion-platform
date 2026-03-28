from __future__ import annotations

from typing import Any


def explain_transfer_action(action: dict[str, Any]) -> str:
    return (
        f"Predicted demand pressure will exceed available stock at warehouse "
        f"{action.get('recipient_warehouse')} for SKU {action.get('sku_id')}. "
        f"Transfer {action.get('transfer_qty')} units from warehouse "
        f"{action.get('donor_warehouse')} to reduce stockout risk from "
        f"{action.get('stockout_risk_before')} to {action.get('stockout_risk_after')}. "
        f"Expected transfer ETA is {action.get('estimated_transfer_mins')} minutes "
        f"with an estimated SLA improvement of {action.get('sla_improvement_pct')}%."
    )


def explain_reorder_action(action: dict[str, Any]) -> str:
    return (
        f"No suitable donor warehouse was available for SKU {action.get('sku_id')} "
        f"to replenish warehouse {action.get('recipient_warehouse')}. "
        f"Recommend reordering {action.get('transfer_qty')} units to protect inventory "
        f"and reduce stockout risk from {action.get('stockout_risk_before')} "
        f"to {action.get('stockout_risk_after')}."
    )


def summarize_run(actions: list[dict[str, Any]], risks: list[dict[str, Any]]) -> dict[str, Any]:
    total_actions = len(actions)
    transfer_actions = sum(1 for a in actions if a.get("action") == "transfer")
    reorder_actions = sum(1 for a in actions if a.get("action") == "reorder")
    high_risk_items = sum(1 for r in risks if r.get("risk_label") == "high")

    return {
        "total_actions": total_actions,
        "transfer_actions": transfer_actions,
        "reorder_actions": reorder_actions,
        "high_risk_items": high_risk_items,
    }