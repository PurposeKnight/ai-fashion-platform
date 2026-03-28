"""
Agentic Inventory Orchestration System for Zintoo
Autonomous agent that reallocates inventory based on demand forecasts
"""
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from models import AgentAction, AgentLog, InventoryReallocation
from database import get_db


class InventoryOptimizationAgent:
    """Agent responsible for autonomous inventory reallocation"""
    
    def __init__(self, agent_id: str = None):
        self.agent_id = agent_id or f"AGENT-{uuid.uuid4().hex[:8].upper()}"
        self.db = get_db()
        self.actions_taken: List[AgentAction] = []
    
    def analyze_demand_forecasts(self, pincode: str, hours_ahead: int = 6) -> Dict[str, float]:
        """
        Analyze demand forecasts for a pincode
        Returns predicted demand by SKU
        """
        forecasts = self.db.get_forecasts('*', pincode, limit=100)
        
        demand_by_sku = {}
        for forecast in forecasts:
            if forecast.sku not in demand_by_sku:
                demand_by_sku[forecast.sku] = 0
            demand_by_sku[forecast.sku] += forecast.predicted_demand
        
        return demand_by_sku
    
    def find_critical_stock_levels(self, pincode: str) -> List[Dict[str, Any]]:
        """
        Identify SKUs with stock levels below forecast demand
        Returns list of critical SKUs
        """
        inventory = self.db.get_inventory_by_pincode(pincode)
        forecasted_demand = self.analyze_demand_forecasts(pincode)
        
        critical_skus = []
        for inv in inventory:
            if inv.sku in forecasted_demand:
                ratio = inv.current_stock / (forecasted_demand[inv.sku] + 1)
                if ratio < 0.5:  # Stock < 50% of forecasted demand
                    critical_skus.append({
                        "sku": inv.sku,
                        "warehouse_id": inv.warehouse_id,
                        "current_stock": inv.current_stock,
                        "forecasted_demand": forecasted_demand[inv.sku],
                        "criticality_score": 1 - ratio
                    })
        
        return sorted(critical_skus, key=lambda x: x['criticality_score'], reverse=True)
    
    def find_donor_warehouses(self, sku: str, target_pincode: str, required_quantity: int) -> List[Dict[str, Any]]:
        """
        Find warehouses with excess inventory for a SKU
        Returns sorted list of donor warehouses
        """
        all_inventory = self.db.get_inventory_by_pincode(target_pincode)
        # Extended search to all warehouses
        donors = []
        
        # Simple implementation: find warehouses with stock > reorder_threshold + buffer
        all_warehouses = set(inv.warehouse_id for inv in all_inventory)
        
        for warehouse_id in list(all_warehouses)[:5]:  # Check first 5 warehouses
            inv_stock = self.db.get_inventory_for_warehouse(warehouse_id)
            for inv in inv_stock:
                if inv.sku == sku and inv.current_stock > (inv.reorder_threshold + 5):
                    donors.append({
                        "warehouse_id": warehouse_id,
                        "available_quantity": inv.current_stock - inv.reorder_threshold,
                        "distance_score": 0.5  # Simplified
                    })
        
        return sorted(donors, key=lambda x: x['available_quantity'], reverse=True)
    
    def generate_reallocation_decision(self, pincode: str) -> List[InventoryReallocation]:
        """
        Generate reallocation decisions based on demand forecast
        """
        critical_skus = self.find_critical_stock_levels(pincode)
        reallocations = []
        
        for critical_sku in critical_skus[:5]:  # Process top 5 critical SKUs
            sku = critical_sku['sku']
            required = int(critical_sku['forecasted_demand'] - critical_sku['current_stock'] + 5)
            
            if required <= 0:
                continue
            
            donors = self.find_donor_warehouses(sku, pincode, required)
            
            for donor in donors:
                if required <= 0:
                    break
                
                transfer_qty = min(donor['available_quantity'], required)
                
                reallocation = InventoryReallocation(
                    source_warehouse=donor['warehouse_id'],
                    destination_warehouse=critical_sku['warehouse_id'],
                    sku=sku,
                    product_id=sku.split('_')[0],  # Extract product from SKU
                    quantity=transfer_qty,
                    reason=f"Demand forecast spike detected for {sku} in pincode {pincode}",
                    forecasted_demand=critical_sku['forecasted_demand'],
                    status="pending"
                )
                reallocations.append(reallocation)
                required -= transfer_qty
        
        return reallocations
    
    def execute_reallocations(self, reallocations: List[InventoryReallocation]) -> List[Dict[str, Any]]:
        """
        Execute reallocations and update database
        """
        execution_results = []
        
        for reallocation in reallocations:
            try:
                # Deduct from source
                self.db.deduct_stock(
                    reallocation.source_warehouse,
                    reallocation.sku,
                    reallocation.quantity
                )
                
                # Add to destination
                self.db.add_stock(
                    reallocation.destination_warehouse,
                    reallocation.sku,
                    reallocation.quantity
                )
                
                # Record reallocation
                reallocation.status = "completed"
                self.db.insert_reallocation(reallocation.dict())
                
                # Log action
                action = AgentAction(
                    action_id=f"ACT-{uuid.uuid4().hex[:8].upper()}",
                    action_type="reallocation",
                    trigger="demand_forecast",
                    skus_affected=[reallocation.sku],
                    warehouses_affected=[reallocation.source_warehouse, reallocation.destination_warehouse],
                    decision_rationale=f"Transferred {reallocation.quantity} units of {reallocation.sku} from {reallocation.source_warehouse} to {reallocation.destination_warehouse} due to forecast demand spike",
                    status="executed"
                )
                self.actions_taken.append(action)
                
                execution_results.append({
                    "status": "success",
                    "reallocation_id": reallocation.reallocation_id,
                    "message": f"Successfully transferred {reallocation.quantity} units"
                })
            
            except Exception as e:
                execution_results.append({
                    "status": "failed",
                    "reallocation_id": reallocation.reallocation_id,
                    "error": str(e)
                })
        
        return execution_results
    
    def optimize_for_pincode(self, pincode: str) -> Dict[str, Any]:
        """
        Complete optimization workflow for a pincode
        """
        start_time = datetime.utcnow()
        
        # Generate decisions
        reallocations = self.generate_reallocation_decision(pincode)
        
        # Execute reallocations
        results = self.execute_reallocations(reallocations)
        
        end_time = datetime.utcnow()
        execution_time_ms = (end_time - start_time).total_seconds() * 1000
        
        # Create and store agent log
        log = AgentLog(
            log_id=f"LOG-{uuid.uuid4().hex[:8].upper()}",
            agent_id=self.agent_id,
            actions=self.actions_taken,
            summary=f"Optimized inventory for pincode {pincode}. Executed {len([r for r in results if r['status'] == 'success'])} reallocations.",
            execution_time_ms=execution_time_ms
        )
        
        self.db.insert_agent_log(log)
        
        return {
            "agent_id": self.agent_id,
            "pincode": pincode,
            "total_reallocations": len(reallocations),
            "successful_reallocations": len([r for r in results if r['status'] == 'success']),
            "failed_reallocations": len([r for r in results if r['status'] == 'failed']),
            "execution_time_ms": execution_time_ms,
            "results": results
        }
    
    def monitor_sla_compliance(self) -> Dict[str, Any]:
        """
        Monitor SLA compliance and trigger optimizations if needed
        """
        # Get recent orders with issues
        pending_orders = self.db.get_orders_by_status("pending", limit=20)
        
        sla_at_risk = []
        for order in pending_orders:
            time_elapsed = (datetime.utcnow() - order.created_at).total_seconds() / 60
            if time_elapsed > 30:  # More than 30 minutes
                sla_at_risk.append({
                    "order_id": order.order_id,
                    "pincode": order.pincode,
                    "time_elapsed_minutes": time_elapsed
                })
        
        # Trigger optimization for affected pincodes
        affected_pincodes = set(o['pincode'] for o in sla_at_risk)
        
        optimization_results = []
        for pincode in affected_pincodes:
            result = self.optimize_for_pincode(pincode)
            optimization_results.append(result)
        
        return {
            "orders_at_risk": len(sla_at_risk),
            "affected_pincodes": list(affected_pincodes),
            "optimizations_triggered": len(optimization_results),
            "optimization_results": optimization_results
        }


def create_agent() -> InventoryOptimizationAgent:
    """Factory function to create an inventory optimization agent"""
    return InventoryOptimizationAgent()
