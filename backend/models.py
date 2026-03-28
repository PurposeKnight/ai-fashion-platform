"""
MongoDB Models and Pydantic Schemas for Zintoo
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


# ==================== PRODUCT MODELS ====================
class ProductSize(str, Enum):
    XS = "XS"
    S = "S"
    M = "M"
    L = "L"
    XL = "XL"
    XXL = "XXL"


class ProductCategory(str, Enum):
    CASUAL = "casual"
    FORMAL = "formal"
    SPORTS = "sports"
    ETHNIC = "ethnic"
    PARTY = "party"


class Product(BaseModel):
    product_id: str = Field(..., description="Unique product ID")
    sku: str = Field(..., description="Stock Keeping Unit")
    name: str
    category: ProductCategory
    description: str
    price: float
    image_url: str
    embedding: Optional[List[float]] = None
    color: str
    size: ProductSize
    material: str
    brand: str
    rating: float = 4.0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "product_id": "prod_001",
                "sku": "KURTA_001_M_BLU",
                "name": "Casual College Kurta",
                "category": "casual",
                "description": "Comfortable cotton kurta perfect for college fests",
                "price": 599.99,
                "image_url": "http://example.com/img.jpg",
                "color": "blue",
                "size": "M",
                "material": "cotton",
                "brand": "ZintooFashion",
            }
        }


# ==================== INVENTORY MODELS ====================
class WarehouseInventory(BaseModel):
    warehouse_id: str = Field(..., description="Unique warehouse ID")
    pincode: str = Field(..., description="5-digit pincode")
    sku: str
    product_id: str
    current_stock: int = 0
    reorder_threshold: int = 10
    last_restock: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "warehouse_id": "W1",
                "pincode": "110001",
                "sku": "KURTA_001_M_BLU",
                "product_id": "prod_001",
                "current_stock": 25,
                "reorder_threshold": 10,
            }
        }


class InventoryReallocation(BaseModel):
    reallocation_id: str = Field(default_factory=lambda: str(datetime.utcnow().timestamp()))
    source_warehouse: str
    destination_warehouse: str
    sku: str
    product_id: str
    quantity: int
    reason: str
    forecasted_demand: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: str = "pending"


# ==================== DEMAND FORECAST MODELS ====================
class DemandForecast(BaseModel):
    forecast_id: str
    sku: str
    product_id: str
    pincode: str
    timestamp: datetime
    forecast_hour: int
    forecast_date: str
    predicted_demand: float
    confidence_interval_lower: float
    confidence_interval_upper: float
    factors: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DemandContext(BaseModel):
    pincode: str
    timestamp: datetime
    temperature: float
    humidity: float
    weather_condition: str
    is_weekend: bool
    is_holiday: bool
    local_events: List[str] = Field(default_factory=list)
    day_of_week: int
    hour_of_day: int


# ==================== RECOMMENDATION MODELS ====================
class RecommendationQuery(BaseModel):
    text_input: Optional[str] = None
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    pincode: str = Field(..., description="User's pincode")
    top_k: int = 10
    filters: Dict[str, Any] = Field(default_factory=dict)


class RecommendationResult(BaseModel):
    product: Product
    similarity_score: float
    availability_in_pincode: int
    estimated_delivery_time: str = "< 60 minutes"
    rank: int


class RecommendationResponse(BaseModel):
    query_id: str
    recommendations: List[RecommendationResult]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ==================== ORDER MODELS ====================
class OrderItem(BaseModel):
    product_id: str
    sku: str
    quantity: int
    price: float


class Order(BaseModel):
    order_id: str
    customer_id: str
    items: List[OrderItem]
    pincode: str
    warehouse_id: str
    total_amount: float
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    delivered_at: Optional[datetime] = None
    returned_at: Optional[datetime] = None
    return_reason: Optional[str] = None


# ==================== AGENT LOG MODELS ====================
class AgentAction(BaseModel):
    action_id: str
    action_type: str
    trigger: str
    skus_affected: List[str]
    warehouses_affected: List[str]
    decision_rationale: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: str = "pending"


class AgentLog(BaseModel):
    log_id: str
    agent_id: str
    actions: List[AgentAction]
    summary: str
    execution_time_ms: float
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ==================== METRICS MODELS ====================
class RecommendationMetrics(BaseModel):
    precision_at_k: Dict[int, float]
    ndcg: float
    mrr: float
    coverage: float
    diversity: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ForecastMetrics(BaseModel):
    mape: float
    rmse: float
    mae: float
    pincode: str
    sku: str
    evaluation_period: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SLAMetrics(BaseModel):
    total_orders: int
    successful_deliveries: int
    sla_breaches: int
    fulfilment_rate: float
    avg_delivery_time_minutes: float
    reallocation_effectiveness: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
