from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.schemas import ForecastRequest, ForecastResponse
from app.data.synthetic.catalogue import generate_catalogue
from app.data.synthetic.demand import generate_demand_history
from app.data.synthetic.warehouses import generate_warehouses
from app.forecasting.predict import predict_forecast

router = APIRouter()

# Temporary in-memory synthetic data for route testing
_catalogue = generate_catalogue(300)
_warehouses = generate_warehouses(8)
_demand_history = generate_demand_history(_catalogue, _warehouses, days=30)


@router.post("/", response_model=ForecastResponse)
def forecast_route(request: ForecastRequest) -> ForecastResponse:
    try:
        result = predict_forecast(
            sku_id=request.sku_id,
            pincode=request.pincode,
            horizon_hours=request.horizon_hours,
            demand_history=_demand_history,
        )
        return ForecastResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))