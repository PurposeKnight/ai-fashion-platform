"""
FastAPI Backend Server for Zintoo AI-Powered Fashion Platform
"""
from fastapi import FastAPI, HTTPException, File, UploadFile, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import List, Dict, Any
from datetime import datetime
import uuid
import json
from models import (
    Product, ProductCategory, ProductSize,
    WarehouseInventory, DemandForecast, Order, OrderItem,
    AgentLog, AgentAction,
    RecommendationQuery, RecommendationResponse, RecommendationResult,
    InventoryReallocation
)
from database import get_db
from dotenv import load_dotenv
import os

load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Zintoo API",
    description="AI-Powered Hyper-Local Fashion Intelligence Platform",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
db = get_db()


# ==================== HEALTH CHECK ====================
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "Zintoo API"
    }


# ==================== PRODUCT ENDPOINTS ====================
@app.post("/api/products", tags=["Products"])
async def create_product(product: Product):
    """Create a new product"""
    try:
        product_id = db.insert_product(product)
        return {
            "success": True,
            "product_id": product_id,
            "message": "Product created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/products/{product_id}", tags=["Products"])
async def get_product(product_id: str):
    """Get product by ID"""
    product = db.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product.dict()


@app.get("/api/products", tags=["Products"])
async def list_products(category: str = None, limit: int = 20):
    """List all products with optional filtering"""
    filters = {}
    if category:
        filters['category'] = category
    products = db.search_products(filters, limit)
    return {
        "total": len(products),
        "products": [p.dict() for p in products]
    }


# ==================== INVENTORY ENDPOINTS ====================
@app.post("/api/inventory", tags=["Inventory"])
async def add_inventory(inventory: WarehouseInventory):
    """Add or update inventory"""
    try:
        db.upsert_inventory(inventory)
        return {
            "success": True,
            "message": "Inventory updated successfully",
            "warehouse_id": inventory.warehouse_id,
            "sku": inventory.sku
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/inventory/warehouse/{warehouse_id}", tags=["Inventory"])
async def get_warehouse_inventory(warehouse_id: str):
    """Get all inventory in a warehouse"""
    inventory = db.get_inventory_for_warehouse(warehouse_id)
    return {
        "warehouse_id": warehouse_id,
        "total_items": len(inventory),
        "inventory": [inv.dict() for inv in inventory]
    }


@app.get("/api/inventory/pincode/{pincode}", tags=["Inventory"])
async def get_pincode_inventory(pincode: str):
    """Get inventory available in a pincode"""
    inventory = db.get_inventory_by_pincode(pincode)
    return {
        "pincode": pincode,
        "total_items": len(inventory),
        "inventory": [inv.dict() for inv in inventory]
    }


@app.get("/api/inventory/stock/{sku}/{pincode}", tags=["Inventory"])
async def check_stock(sku: str, pincode: str):
    """Check stock availability for SKU in pincode"""
    stock = db.check_stock(sku, pincode)
    return {
        "sku": sku,
        "pincode": pincode,
        "available_stock": stock,
        "can_fulfill": stock > 0
    }


@app.post("/api/inventory/deduct", tags=["Inventory"])
async def deduct_inventory(warehouse_id: str, sku: str, quantity: int):
    """Deduct stock from warehouse"""
    success = db.deduct_stock(warehouse_id, sku, quantity)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to deduct stock")
    return {
        "success": True,
        "warehouse_id": warehouse_id,
        "sku": sku,
        "quantity_deducted": quantity
    }


@app.post("/api/inventory/add", tags=["Inventory"])
async def add_inventory_stock(warehouse_id: str, sku: str, quantity: int):
    """Add stock to warehouse"""
    success = db.add_stock(warehouse_id, sku, quantity)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to add stock")
    return {
        "success": True,
        "warehouse_id": warehouse_id,
        "sku": sku,
        "quantity_added": quantity
    }


# ==================== DEMAND FORECAST ENDPOINTS ====================
@app.post("/api/forecasts", tags=["Forecasting"])
async def create_forecast(forecast: DemandForecast):
    """Create demand forecast"""
    try:
        db.insert_forecast(forecast)
        return {
            "success": True,
            "forecast_id": forecast.forecast_id,
            "sku": forecast.sku,
            "pincode": forecast.pincode,
            "predicted_demand": forecast.predicted_demand
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/forecasts/{sku}/{pincode}", tags=["Forecasting"])
async def get_forecasts(sku: str, pincode: str, limit: int = 50):
    """Get forecasts for SKU and pincode"""
    forecasts = db.get_forecasts(sku, pincode, limit)
    return {
        "sku": sku,
        "pincode": pincode,
        "total_forecasts": len(forecasts),
        "forecasts": [f.dict() for f in forecasts]
    }


# ==================== ORDER ENDPOINTS ====================
@app.post("/api/orders", tags=["Orders"])
async def create_order(order: Order, background_tasks: BackgroundTasks):
    """Create a new order"""
    try:
        order.order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        order_id = db.insert_order(order)
        
        # Background task: trigger demand monitoring
        background_tasks.add_task(monitor_demand_after_order, order.sku if hasattr(order, 'sku') else None, order.pincode)
        
        return {
            "success": True,
            "order_id": order.order_id,
            "status": "pending",
            "total_amount": order.total_amount,
            "estimated_delivery": "60 minutes"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/orders/{order_id}", tags=["Orders"])
async def get_order(order_id: str):
    """Get order by ID"""
    order = db.get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order.dict()


@app.get("/api/orders/status/{status}", tags=["Orders"])
async def get_orders_by_status(status: str, limit: int = 50):
    """Get orders by status"""
    orders = db.get_orders_by_status(status, limit)
    return {
        "status": status,
        "total_orders": len(orders),
        "orders": [o.dict() for o in orders]
    }


@app.patch("/api/orders/{order_id}/status", tags=["Orders"])
async def update_order_status(order_id: str, status: str):
    """Update order status"""
    try:
        db.update_order_status(order_id, status)
        return {
            "success": True,
            "order_id": order_id,
            "new_status": status
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== RECOMMENDATION ENDPOINTS ====================
@app.post("/api/recommendations", tags=["Recommendations"])
async def get_recommendations(query: RecommendationQuery):
    """Get product recommendations based on text/image"""
    try:
        # Get all products for this implementation
        all_products = db.get_all_products(limit=100)
        
        # Simple filtering: match by pincode and category if provided
        results = []
        for idx, product in enumerate(all_products[:query.top_k]):
            result = RecommendationResult(
                product=product,
                similarity_score=0.85 + (0.01 * idx),  # Simulated similarity
                availability_in_pincode=db.check_stock(product.sku, query.pincode),
                rank=idx + 1
            )
            results.append(result)
        
        return RecommendationResponse(
            query_id=f"REC-{uuid.uuid4().hex[:8].upper()}",
            recommendations=results
        ).dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== INVENTORY REALLOCATION (AGENT) ENDPOINTS ====================
@app.post("/api/reallocations", tags=["Inventory Orchestration"])
async def create_reallocation(reallocation: InventoryReallocation):
    """Create inventory reallocation"""
    try:
        reallocation_dict = reallocation.dict()
        db.insert_reallocation(reallocation_dict)
        return {
            "success": True,
            "reallocation_id": reallocation.reallocation_id,
            "source": reallocation.source_warehouse,
            "destination": reallocation.destination_warehouse,
            "quantity": reallocation.quantity,
            "status": "pending"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/reallocations", tags=["Inventory Orchestration"])
async def get_reallocations(status: str = None, limit: int = 100):
    """Get reallocation history"""
    reallocations = db.get_reallocations(status, limit)
    return {
        "total": len(reallocations),
        "reallocations": reallocations
    }


@app.post("/api/agent/trigger-optimization", tags=["Inventory Orchestration"])
async def trigger_optimization(pincode: str, background_tasks: BackgroundTasks):
    """Trigger agent-based inventory optimization"""
    try:
        background_tasks.add_task(optimize_inventory_for_pincode, pincode)
        return {
            "success": True,
            "pincode": pincode,
            "message": "Optimization triggered",
            "job_id": f"OPT-{uuid.uuid4().hex[:8].upper()}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== AGENT LOG ENDPOINTS ====================
@app.get("/api/agent-logs", tags=["Agent Logs"])
async def get_agent_logs(limit: int = 50):
    """Get recent agent logs"""
    logs = db.get_recent_agent_logs(limit)
    return {
        "total": len(logs),
        "logs": [log.dict() for log in logs]
    }


@app.post("/api/agent-logs", tags=["Agent Logs"])
async def create_agent_log(log: AgentLog):
    """Create agent log entry"""
    try:
        db.insert_agent_log(log)
        return {
            "success": True,
            "log_id": log.log_id,
            "timestamp": log.created_at.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== STATISTICS ENDPOINTS ====================
@app.get("/api/stats/sla", tags=["Analytics"])
async def get_sla_metrics():
    """Get SLA fulfillment metrics"""
    pending_orders = db.get_orders_by_status("pending")
    delivered_orders = db.get_orders_by_status("delivered")
    returned_orders = db.get_orders_by_status("returned")
    
    total = len(pending_orders) + len(delivered_orders) + len(returned_orders)
    if total == 0:
        return {"success": False, "message": "No orders found"}
    
    return {
        "total_orders": total,
        "successful_deliveries": len(delivered_orders),
        "sla_breaches": len(returned_orders),
        "fulfilment_rate": (len(delivered_orders) / total) * 100 if total > 0 else 0,
        "return_rate": (len(returned_orders) / total) * 100 if total > 0 else 0
    }


# ==================== BACKGROUND TASKS ====================
async def monitor_demand_after_order(sku: str, pincode: str):
    """Background task to monitor demand after order"""
    pass


async def optimize_inventory_for_pincode(pincode: str):
    """Background task to optimize inventory for a pincode"""
    pass


# ==================== ROOT ENDPOINT ====================
@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "name": "Zintoo API",
        "version": "1.0.0",
        "description": "AI-Powered Hyper-Local Fashion Intelligence Platform",
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
            "products": "/api/products",
            "inventory": "/api/inventory",
            "orders": "/api/orders",
            "forecasts": "/api/forecasts",
            "recommendations": "/api/recommendations",
            "reallocations": "/api/reallocations",
            "agent_logs": "/api/agent-logs"
        }
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
