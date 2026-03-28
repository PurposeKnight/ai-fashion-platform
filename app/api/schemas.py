from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


# =========================================================
# Shared / reusable models
# =========================================================

class ProductCard(BaseModel):
    product_id: str
    sku_id: str
    name: str
    category: str
    sub_category: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    color_family: Optional[str] = None
    gender: Optional[str] = None
    season: Optional[str] = None
    occasion: Optional[str] = None
    material: Optional[str] = None
    fit: Optional[str] = None
    pattern: Optional[str] = None
    style_tags: list[str] = Field(default_factory=list)
    price: float

    popularity_score: Optional[float] = None
    return_rate: Optional[float] = None

    image_url: Optional[str] = None
    metadata_text: Optional[str] = None

    retrieval_score: Optional[float] = None
    final_score: Optional[float] = None
    matched_attributes: list[str] = Field(default_factory=list)

    warehouse_id: Optional[str] = None
    available_stock: Optional[int] = None
    estimated_delivery_mins: Optional[int] = None


class ForecastPoint(BaseModel):
    timestamp_hour: str
    predicted_demand: float
    lower_bound: float
    upper_bound: float
    risk_level: Literal["low", "medium", "high"]
    top_drivers: list[str] = Field(default_factory=list)


class RiskSummaryItem(BaseModel):
    warehouse_id: str
    pincode: str
    sku_id: str
    product_id: Optional[str] = None
    available_stock: float
    projected_deficit: float
    stockout_risk: float
    sla_risk: float
    risk_label: Literal["low", "medium", "high"]


class ActionItem(BaseModel):
    action: Literal["transfer", "reorder"]
    sku_id: str
    product_id: Optional[str] = None

    recipient_warehouse: str
    recipient_pincode: Optional[str] = None

    donor_warehouse: Optional[str] = None

    transfer_qty: int
    distance_km: Optional[float] = None
    estimated_transfer_mins: Optional[int] = None
    transfer_cost: Optional[float] = None

    stockout_risk_before: float
    stockout_risk_after: float
    sla_risk_before: float
    sla_risk_after: float
    sla_improvement_pct: float

    decision_score: Optional[float] = None
    status: Optional[str] = None
    explanation: Optional[str] = None


class RunSummary(BaseModel):
    total_actions: int
    transfer_actions: int
    reorder_actions: int
    high_risk_items: int


# =========================================================
# Recommendation request / response
# =========================================================

class RecommendationRequest(BaseModel):
    text_query: Optional[str] = None
    pincode: Optional[str] = None
    top_k: int = 5

    price_min: Optional[float] = None
    price_max: Optional[float] = None
    price_intent: Optional[Literal["budget", "mid", "premium"]] = "mid"

    category_filter: Optional[list[str]] = None
    preferred_colors: Optional[list[str]] = None
    occasion: Optional[str] = None
    gender: Optional[str] = None

    mode: Optional[Literal["text", "image", "multimodal"]] = "text"


class RecommendationResponse(BaseModel):
    mode: Literal["text", "image", "multimodal"]
    count: int
    results: list[ProductCard] = Field(default_factory=list)


# =========================================================
# Forecast request / response
# =========================================================

class ForecastRequest(BaseModel):
    sku_id: str
    pincode: str
    horizon_hours: int = 6


class ForecastResponse(BaseModel):
    sku_id: str
    pincode: str
    horizon_hours: int
    forecast: list[ForecastPoint] = Field(default_factory=list)


# =========================================================
# Risk request / response
# =========================================================

class RiskRequest(BaseModel):
    pincode: Optional[str] = None
    sku_id: Optional[str] = None


class RiskResponse(BaseModel):
    risks: list[RiskSummaryItem] = Field(default_factory=list)


# =========================================================
# Orchestration request / response
# =========================================================

class OrchestrationRequest(BaseModel):
    pincode: Optional[str] = None
    sku_id: Optional[str] = None
    dry_run: bool = False


class OrchestrationResponse(BaseModel):
    actions: list[ActionItem] = Field(default_factory=list)
    risks: list[RiskSummaryItem] = Field(default_factory=list)
    summary: RunSummary


# =========================================================
# Simulation request / response
# =========================================================

class SimulationRequest(BaseModel):
    text_query: Optional[str] = None
    pincode: str
    top_k: int = 5

    price_min: Optional[float] = None
    price_max: Optional[float] = None
    price_intent: Optional[Literal["budget", "mid", "premium"]] = "mid"

    selected_rank: int = 1
    dry_run: bool = True


class SimulationResponse(BaseModel):
    recommendation: RecommendationResponse
    selected_product: Optional[ProductCard] = None
    forecast: Optional[ForecastResponse] = None
    orchestration: Optional[OrchestrationResponse] = None
    message: Optional[str] = None