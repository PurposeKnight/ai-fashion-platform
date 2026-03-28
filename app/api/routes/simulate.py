from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.schemas import (
    ForecastResponse,
    OrchestrationResponse,
    RecommendationRequest,
    RecommendationResponse,
    SimulationRequest,
    SimulationResponse,
)
from app.data.synthetic.catalogue import generate_catalogue
from app.data.synthetic.demand import generate_demand_history
from app.data.synthetic.warehouses import (
    generate_inventory,
    generate_transfer_matrix,
    generate_warehouses,
)
from app.forecasting.predict import predict_forecast
from app.orchestration.pipeline import run_orchestration
from app.recommender.pipeline import recommend_by_text

router = APIRouter()

# Temporary in-memory synthetic data for route testing
_catalogue = generate_catalogue(300)
_warehouses = generate_warehouses(8)
_inventory = generate_inventory(_catalogue, _warehouses)
_transfer_matrix = generate_transfer_matrix(_warehouses)
_demand_history = generate_demand_history(_catalogue, _warehouses, days=30)


@router.post("/order", response_model=SimulationResponse)
def simulate_order(request: SimulationRequest) -> SimulationResponse:
    try:
        # 1. Recommendation
        rec_request = RecommendationRequest(
            text_query=request.text_query,
            pincode=request.pincode,
            top_k=request.top_k,
            price_min=request.price_min,
            price_max=request.price_max,
            price_intent=request.price_intent,
            mode="text",
        )

        rec_result = recommend_by_text(
            request=rec_request,
            catalogue=_catalogue,
            inventory=_inventory,
        )
        recommendation = RecommendationResponse(**rec_result)

        if not recommendation.results:
            return SimulationResponse(
                recommendation=recommendation,
                selected_product=None,
                forecast=None,
                orchestration=None,
                message="No recommendation results found.",
            )

        # 2. Pick selected or top SKU
        selected_index = max(0, request.selected_rank - 1)
        if selected_index >= len(recommendation.results):
            selected_index = 0

        selected_product = recommendation.results[selected_index]
        selected_sku = selected_product.sku_id

        # 3. Forecast for selected SKU and pincode
        forecast_result = predict_forecast(
            sku_id=selected_sku,
            pincode=request.pincode,
            horizon_hours=6,
            demand_history=_demand_history,
        )
        forecast = ForecastResponse(**forecast_result)

        # 4. Orchestration
        orchestration_result = run_orchestration(
            inventory=_inventory,
            transfer_matrix=_transfer_matrix,
            demand_history=_demand_history,
            pincode=request.pincode,
            sku_id=selected_sku,
            dry_run=request.dry_run,
        )
        orchestration = OrchestrationResponse(**orchestration_result)

        # 5. Return end-to-end response
        return SimulationResponse(
            recommendation=recommendation,
            selected_product=selected_product,
            forecast=forecast,
            orchestration=orchestration,
            message="Simulation completed successfully.",
        )

    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))