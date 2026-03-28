"""
Automatic inventory restocking system
Monitors inventory levels and automatically triggers restocking when stock is low
"""
import threading
import logging
from datetime import datetime
from typing import List, Dict, Any
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

class AutoRestockingSystem:
    """Handles automatic restocking of low inventory items"""
    
    def __init__(self, db, restock_threshold: int = 20, check_interval_minutes: int = 5):
        """
        Initialize the auto-restocking system
        
        Args:
            db: Database connection instance
            restock_threshold: Trigger restock when stock falls below this level
            check_interval_minutes: How often to check inventory (in minutes)
        """
        self.db = db
        self.restock_threshold = restock_threshold
        self.check_interval_minutes = check_interval_minutes
        self.scheduler = None
        self.lock = threading.Lock()
        self.restock_history = []  # Track recent restocking actions
        
    def start(self):
        """Start the automatic restocking scheduler"""
        if self.scheduler is not None:
            logger.warning("Auto-restocking system is already running")
            return
        
        try:
            self.scheduler = BackgroundScheduler()
            self.scheduler.add_job(
                self.check_and_restock,
                trigger=IntervalTrigger(minutes=self.check_interval_minutes),
                id='auto_restock_job',
                name='Automatic Inventory Restocking',
                replace_existing=True
            )
            self.scheduler.start()
            logger.info(f"Auto-restocking system started (checks every {self.check_interval_minutes} minutes, threshold: {self.restock_threshold})")
        except Exception as e:
            logger.error(f"Failed to start auto-restocking system: {e}")
    
    def stop(self):
        """Stop the automatic restocking scheduler"""
        if self.scheduler is not None:
            try:
                self.scheduler.shutdown()
                self.scheduler = None
                logger.info("Auto-restocking system stopped")
            except Exception as e:
                logger.error(f"Error stopping auto-restocking system: {e}")
    
    def check_and_restock(self):
        """Check all inventory levels and trigger restocking for low stock items"""
        with self.lock:
            try:
                logger.info(f"[AUTO-RESTOCK] Starting inventory check at {datetime.utcnow().isoformat()}")
                
                # Get all inventory - try direct MongoDB access first
                all_inventory = []
                
                # Direct MongoDB query
                if hasattr(self.db, 'db') and self.db.db is not None:
                    try:
                        docs = list(self.db.db['inventory'].find())
                        all_inventory = [
                            {
                                'sku': doc.get('sku'),
                                'warehouse_id': doc.get('warehouse_id'),
                                'pincode': doc.get('pincode'),
                                'current_stock': doc.get('current_stock', 0)
                            } for doc in docs
                        ]
                        logger.info(f"[AUTO-RESTOCK] Found {len(all_inventory)} inventory items in MongoDB")
                    except Exception as e:
                        logger.warning(f"[AUTO-RESTOCK] MongoDB direct query failed: {e}")
                
                # Fallback to method call
                if not all_inventory and hasattr(self.db, 'get_all_inventory'):
                    all_inventory = self.db.get_all_inventory()
                
                # Final fallback: get from warehouses
                if not all_inventory:
                    all_inventory = self._get_inventory_from_products()
                
                if not all_inventory:
                    logger.warning("[AUTO-RESTOCK] No inventory data available")
                    return
                
                # Find items below restock threshold
                low_stock_items = [
                    inv for inv in all_inventory 
                    if self._get_stock_level(inv) < self.restock_threshold
                ]
                
                logger.info(f"[AUTO-RESTOCK] Found {len(low_stock_items)} items below threshold ({self.restock_threshold})")
                
                # Log low stock items for debugging
                for item in low_stock_items:
                    stock_level = self._get_stock_level(item)
                    logger.info(f"[AUTO-RESTOCK]   - {item.get('sku')}: {stock_level} units")
                
                # Generate restock actions
                actions = self._generate_restock_actions(low_stock_items)
                
                if actions:
                    logger.info(f"[AUTO-RESTOCK] Generated {len(actions)} restock actions")
                    self._execute_restock_actions(actions)
                else:
                    logger.info("[AUTO-RESTOCK] No restock actions needed")
                
            except Exception as e:
                logger.error(f"[AUTO-RESTOCK] Error during check_and_restock: {e}", exc_info=True)
    
    def _get_stock_level(self, inventory_item: Dict[str, Any]) -> int:
        """Extract stock level from inventory item"""
        if hasattr(inventory_item, 'available_quantity'):
            return inventory_item.available_quantity
        elif hasattr(inventory_item, 'quantity'):
            return inventory_item.quantity
        elif isinstance(inventory_item, dict):
            return inventory_item.get('available_stock', 0) or inventory_item.get('quantity', 0)
        return 0
    
    def _get_inventory_fallback(self) -> List[Dict[str, Any]]:
        """Fallback method to get inventory if main method fails"""
        try:
            # Try to get inventory from all warehouses
            if hasattr(self.db, 'get_all_warehouses'):
                warehouses = self.db.get_all_warehouses()
                all_inv = []
                for wh_id in warehouses:
                    if hasattr(self.db, 'get_inventory_for_warehouse'):
                        inv = self.db.get_inventory_for_warehouse(wh_id)
                        if inv:
                            all_inv.extend([i.dict() if hasattr(i, 'dict') else i for i in inv])
                return all_inv
        except Exception as e:
            logger.debug(f"[AUTO-RESTOCK] Fallback inventory retrieval failed: {e}")
        return []

    def _get_inventory_from_products(self) -> List[Dict[str, Any]]:
        """Get inventory data from products and warehouses"""
        try:
            all_inv = []
            # Try to get all warehouses and their inventory
            if hasattr(self.db, 'get_all_warehouses'):
                warehouses = self.db.get_all_warehouses()
                logger.debug(f"[AUTO-RESTOCK] Found warehouses: {warehouses}")
                
                for wh_id in warehouses:
                    if hasattr(self.db, 'get_inventory_for_warehouse'):
                        inv = self.db.get_inventory_for_warehouse(wh_id)
                        if inv:
                            for i in inv:
                                item_dict = i.dict() if hasattr(i, 'dict') else i
                                all_inv.append(item_dict)
            return all_inv
        except Exception as e:
            logger.debug(f"[AUTO-RESTOCK] get_inventory_from_products failed: {e}")
        return []
    
    def _generate_restock_actions(self, low_stock_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate restock actions for low stock items"""
        actions = []
        
        for item in low_stock_items:
            try:
                warehouse = self._get_item_value(item, ['warehouse_id', 'warehouse'])
                sku = self._get_item_value(item, ['sku', 'sku_id', 'product_id'])
                pincode = self._get_item_value(item, ['pincode'])
                current_stock = self._get_stock_level(item)
                
                # Calculate restock quantity (aim for higher target level)
                restock_quantity = max(50 - current_stock, 25)  # Restock to ~50 units minimum
                
                action = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "action_type": "auto_transfer",
                    "warehouse_id": warehouse,
                    "sku_id": sku,
                    "pincode": pincode,
                    "current_stock": current_stock,
                    "restock_quantity": restock_quantity,
                    "target_level": 50,
                    "reason": f"Auto-restock: Stock below threshold ({current_stock} < {self.restock_threshold})",
                    "priority": "high" if current_stock < 10 else "medium",
                    "source_warehouse": "WH-Delhi-A",  # Default source
                    "destination_warehouse": warehouse,
                    "status": "pending"
                }
                actions.append(action)
                
            except Exception as e:
                logger.warning(f"[AUTO-RESTOCK] Failed to generate action for item: {e}")
        
        return actions
    
    def _execute_restock_actions(self, actions: List[Dict[str, Any]]):
        """Execute the generated restock actions"""
        for action in actions:
            try:
                # Log the action
                logger.info(
                    f"[AUTO-RESTOCK] {action['action_type']}: "
                    f"SKU {action['sku_id']} in {action['warehouse_id']} "
                    f"from {action['current_stock']} to {action['current_stock'] + action['restock_quantity']} units"
                )
                
                # Execute the transfer (simplified - in real system would validate availability)
                if hasattr(self.db, 'add_stock'):
                    self.db.add_stock(
                        action['destination_warehouse'],
                        action['sku_id'],
                        action['restock_quantity']
                    )
                    action['status'] = 'completed'
                    logger.info(f"[AUTO-RESTOCK] Successfully restocked {action['sku_id']} in {action['warehouse_id']}")
                else:
                    action['status'] = 'pending_execution'
                    logger.info(f"[AUTO-RESTOCK] Action queued for manual execution: {action}")
                
                # Store in history
                self.restock_history.append(action)
                
            except Exception as e:
                logger.error(f"[AUTO-RESTOCK] Failed to execute action: {e}")
                action['status'] = 'failed'
                action['error'] = str(e)
    
    def _get_item_value(self, item: Any, keys: List[str], default: str = 'Unknown') -> str:
        """Safely extract value from item using multiple possible keys"""
        for key in keys:
            if hasattr(item, key):
                val = getattr(item, key)
                if val:
                    return val
            elif isinstance(item, dict) and key in item:
                val = item.get(key)
                if val:
                    return val
        return default
    
    def get_restock_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent restock actions"""
        return self.restock_history[-limit:]
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the auto-restocking system"""
        return {
            "running": self.scheduler is not None and self.scheduler.running,
            "threshold": self.restock_threshold,
            "check_interval_minutes": self.check_interval_minutes,
            "recent_actions": len(self.restock_history),
            "next_check": None  # Can be populated with scheduler info if needed
        }
