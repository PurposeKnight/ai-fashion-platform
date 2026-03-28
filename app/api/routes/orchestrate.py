from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.schemas import (
    OrchestrationRequest,
    OrchestrationResponse,
    RiskRequest,
    RiskResponse,
)
from app.data.synthetic.catalogue import generate_catalogue
from app.data.synthetic.demand import generate_demand_history
from app.data.synthetic.warehouses import (
    generate_inventory,
    generate_transfer_matrix,
    generate_warehouses,
)
from app.orchestration.pipeline import get_risk_summary, run_orchestration

router = APIRouter()

# Temporary synthetic data for testing
_catalogue = generate_catalogue(300)
_warehouses = generate_warehouses(8)
_inventory = generate_inventory(_catalogue, _warehouses)
_transfer_matrix = generate_transfer_matrix(_warehouses)
_demand_history = generate_demand_history(_catalogue, _warehouses, days=30)


@router.post("/risk", response_model=RiskResponse)
def inventory_risk_route(request: RiskRequest) -> RiskResponse:
    try:
        risks = get_risk_summary(
            inventory=_inventory,
            demand_history=_demand_history,
            pincode=request.pincode,
            sku_id=request.sku_id,
        )
        return RiskResponse(risks=risks)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/orchestrate", response_model=OrchestrationResponse)
def orchestrate_route(request: OrchestrationRequest) -> OrchestrationResponse:
    try:
        result = run_orchestration(
            inventory=_inventory,
            transfer_matrix=_transfer_matrix,
            demand_history=_demand_history,
            pincode=request.pincode,
            sku_id=request.sku_id,
            dry_run=request.dry_run,
        )
        return OrchestrationResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))