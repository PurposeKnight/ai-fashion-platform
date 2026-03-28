"""
MongoDB Database Handler for Zintoo
"""
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from typing import List, Optional, Dict, Any
from models import Product, WarehouseInventory, DemandForecast, Order, AgentLog
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class ZintooDatabase:
    def __init__(self, mongo_uri: str = None):
        self.mongo_uri = mongo_uri or os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.client = None
        self.db = None
        self.initialize()

    def initialize(self):
        """Initialize MongoDB connection"""
        try:
            self.client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
            self.client.admin.command('ping')
            self.db = self.client['zintoo_db']
            self._create_collections()
            print("✓ MongoDB connected successfully")
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            print(f"⚠ MongoDB connection failed: {e}. Using mock mode.")
            self.client = None
            self.db = None

    def _create_collections(self):
        """Create collections and indexes"""
        if self.db is None:
            return

        collections_config = {
            'products': [
                ('product_id', True),
                ('sku', True),
                ('category', False),
            ],
            'inventory': [
                ('warehouse_id', False),
                ('pincode', False),
                ('sku', False),
                ('product_id', False),
            ],
            'demand_forecasts': [
                ('sku', False),
                ('pincode', False),
                ('timestamp', False),
            ],
            'orders': [
                ('order_id', True),
                ('customer_id', False),
                ('pincode', False),
                ('status', False),
            ],
            'agent_logs': [
                ('log_id', True),
                ('agent_id', False),
                ('timestamp', False),
            ],
            'reallocations': [
                ('reallocation_id', True),
                ('source_warehouse', False),
                ('destination_warehouse', False),
                ('status', False),
            ],
        }

        for collection_name, indexes in collections_config.items():
            if collection_name not in self.db.list_collection_names():
                self.db.create_collection(collection_name)
            
            collection = self.db[collection_name]
            for field, unique in indexes:
                try:
                    collection.create_index([(field, 1)], unique=unique, sparse=True)
                except:
                    pass

    # ==================== PRODUCT OPERATIONS ====================
    def insert_product(self, product: Product) -> str:
        """Insert a product"""
        if self.db is None:
            return product.product_id
        result = self.db['products'].insert_one(product.dict())
        return str(result.inserted_id)

    def get_product(self, product_id: str) -> Optional[Product]:
        """Get product by ID"""
        if self.db is None:
            return None
        doc = self.db['products'].find_one({'product_id': product_id})
        if doc:
            doc.pop('_id', None)
            return Product(**doc)
        return None

    def search_products(self, filters: Dict[str, Any], limit: int = 20) -> List[Product]:
        """Search products with filters"""
        if self.db is None:
            return []
        docs = list(self.db['products'].find(filters).limit(limit))
        return [Product(**{k: v for k, v in doc.items() if k != '_id'}) for doc in docs]

    def get_all_products(self, limit: int = 100) -> List[Product]:
        """Get all products"""
        if self.db is None:
            return []
        docs = list(self.db['products'].find().limit(limit))
        return [Product(**{k: v for k, v in doc.items() if k != '_id'}) for doc in docs]

    # ==================== INVENTORY OPERATIONS ====================
    def upsert_inventory(self, inventory: WarehouseInventory):
        """Insert or update inventory"""
        if self.db is None:
            return
        query = {
            'warehouse_id': inventory.warehouse_id,
            'sku': inventory.sku,
            'pincode': inventory.pincode
        }
        self.db['inventory'].update_one(query, {'$set': inventory.dict()}, upsert=True)

    def get_inventory_for_warehouse(self, warehouse_id: str) -> List[WarehouseInventory]:
        """Get all inventory in a warehouse"""
        if self.db is None:
            return []
        docs = list(self.db['inventory'].find({'warehouse_id': warehouse_id}))
        return [WarehouseInventory(**{k: v for k, v in doc.items() if k != '_id'}) for doc in docs]

    def get_inventory_by_pincode(self, pincode: str) -> List[WarehouseInventory]:
        """Get inventory available in a pincode"""
        if self.db is None:
            return []
        docs = list(self.db['inventory'].find({'pincode': pincode}))
        return [WarehouseInventory(**{k: v for k, v in doc.items() if k != '_id'}) for doc in docs]

    def check_stock(self, sku: str, pincode: str) -> int:
        """Check total stock for SKU in pincode"""
        if self.db is None:
            return 0
        inventories = self.get_inventory_by_pincode(pincode)
        return sum(inv.current_stock for inv in inventories if inv.sku == sku)

    def deduct_stock(self, warehouse_id: str, sku: str, quantity: int) -> bool:
        """Deduct stock from warehouse"""
        if self.db is None:
            return True
        result = self.db['inventory'].update_one(
            {'warehouse_id': warehouse_id, 'sku': sku},
            {'$inc': {'current_stock': -quantity}}
        )
        return result.modified_count > 0

    def add_stock(self, warehouse_id: str, sku: str, quantity: int) -> bool:
        """Add stock to warehouse"""
        if self.db is None:
            return True
        result = self.db['inventory'].update_one(
            {'warehouse_id': warehouse_id, 'sku': sku},
            {'$inc': {'current_stock': quantity}}
        )
        return result.modified_count > 0

    # ==================== FORECAST OPERATIONS ====================
    def insert_forecast(self, forecast: DemandForecast):
        """Insert demand forecast"""
        if self.db is None:
            return
        self.db['demand_forecasts'].insert_one(forecast.dict())

    def get_forecasts(self, sku: str, pincode: str, limit: int = 100) -> List[DemandForecast]:
        """Get forecasts for SKU and pincode"""
        if self.db is None:
            return []
        docs = list(self.db['demand_forecasts'].find(
            {'sku': sku, 'pincode': pincode}
        ).sort('timestamp', -1).limit(limit))
        return [DemandForecast(**{k: v for k, v in doc.items() if k != '_id'}) for doc in docs]

    # ==================== ORDER OPERATIONS ====================
    def insert_order(self, order: Order) -> str:
        """Insert order"""
        if self.db is None:
            return order.order_id
        result = self.db['orders'].insert_one(order.dict())
        return str(result.inserted_id)

    def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID"""
        if self.db is None:
            return None
        doc = self.db['orders'].find_one({'order_id': order_id})
        if doc:
            doc.pop('_id', None)
            return Order(**doc)
        return None

    def update_order_status(self, order_id: str, status: str):
        """Update order status"""
        if self.db is None:
            return
        self.db['orders'].update_one(
            {'order_id': order_id},
            {'$set': {'status': status}}
        )

    def get_orders_by_status(self, status: str, limit: int = 50) -> List[Order]:
        """Get orders by status"""
        if self.db is None:
            return []
        docs = list(self.db['orders'].find({'status': status}).limit(limit))
        return [Order(**{k: v for k, v in doc.items() if k != '_id'}) for doc in docs]

    # ==================== AGENT LOG OPERATIONS ====================
    def insert_agent_log(self, log: AgentLog):
        """Insert agent execution log"""
        if self.db is None:
            return
        self.db['agent_logs'].insert_one(log.dict())

    def get_recent_agent_logs(self, limit: int = 50) -> List[AgentLog]:
        """Get recent agent logs"""
        if self.db is None:
            return []
        docs = list(self.db['agent_logs'].find().sort('created_at', -1).limit(limit))
        return [AgentLog(**{k: v for k, v in doc.items() if k != '_id'}) for doc in docs]

    # ==================== REALLOCATION OPERATIONS ====================
    def insert_reallocation(self, reallocation_dict: Dict[str, Any]):
        """Insert reallocation record"""
        if self.db is None:
            return
        self.db['reallocations'].insert_one(reallocation_dict)

    def get_reallocations(self, status: str = None, limit: int = 100) -> List[Dict]:
        """Get reallocation records"""
        if self.db is None:
            return []
        query = {'status': status} if status else {}
        docs = list(self.db['reallocations'].find(query).sort('timestamp', -1).limit(limit))
        return [{k: v for k, v in doc.items() if k != '_id'} for doc in docs]

    def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()


# Global database instance
_db_instance = None

def get_db() -> ZintooDatabase:
    """Get or create global database instance"""
    global _db_instance
    if _db_instance is None:
        _db_instance = ZintooDatabase()
    return _db_instance
