"""
API Testing and Demo Script for Zintoo
Demonstrates all major features
"""
import requests
import json
from typing import Dict, Any
import time

BASE_URL = "http://localhost:8000"

class ZintooAPITester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
    
    def print_section(self, title: str):
        """Print a formatted section header"""
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
    
    def print_response(self, response: requests.Response, description: str = ""):
        """Pretty print API response"""
        status_color = "✓" if response.status_code < 400 else "✗"
        print(f"\n{status_color} {description}")
        print(f"  Status: {response.status_code}")
        try:
            data = response.json()
            print(f"  Response: {json.dumps(data, indent=2)[:500]}...")
        except:
            print(f"  Response: {response.text[:200]}")
    
    # ==================== HEALTH & INFO ====================
    def test_health(self):
        """Test health check endpoint"""
        self.print_section("HEALTH CHECK")
        response = self.session.get(f"{self.base_url}/health")
        self.print_response(response, "Health Check")
        return response.status_code == 200
    
    def test_root(self):
        """Test root endpoint"""
        response = self.session.get(f"{self.base_url}/")
        self.print_response(response, "API Info")
        return response.status_code == 200
    
    # ==================== PRODUCT ENDPOINTS ====================
    def test_create_product(self) -> Dict[str, Any]:
        """Create a test product"""
        self.print_section("PRODUCT MANAGEMENT")
        
        product_data = {
            "product_id": "prod_demo_001",
            "sku": "DEMO_KURTA_M_BLU",
            "name": "Demo Blue Casual Kurta",
            "category": "casual",
            "description": "Test kurta for demo",
            "price": 699.99,
            "image_url": "http://example.com/demo.jpg",
            "color": "blue",
            "size": "M",
            "material": "cotton",
            "brand": "ZintooDemo"
        }
        
        response = self.session.post(
            f"{self.base_url}/api/products",
            json=product_data
        )
        self.print_response(response, "Create Product")
        return product_data if response.status_code == 200 else None
    
    def test_get_products(self):
        """List products"""
        response = self.session.get(f"{self.base_url}/api/products?limit=5")
        self.print_response(response, "List Products")
        return response.json() if response.status_code == 200 else None
    
    # ==================== INVENTORY ENDPOINTS ====================
    def test_add_inventory(self):
        """Add inventory"""
        self.print_section("INVENTORY MANAGEMENT")
        
        inventory_data = {
            "warehouse_id": "W_DEMO",
            "pincode": "110001",
            "sku": "DEMO_KURTA_M_BLU",
            "product_id": "prod_demo_001",
            "current_stock": 15,
            "reorder_threshold": 5
        }
        
        response = self.session.post(
            f"{self.base_url}/api/inventory",
            json=inventory_data
        )
        self.print_response(response, "Add Inventory")
        return response.status_code == 200
    
    def test_check_stock(self):
        """Check stock availability"""
        response = self.session.get(
            f"{self.base_url}/api/inventory/stock/DEMO_KURTA_M_BLU/110001"
        )
        self.print_response(response, "Check Stock Availability")
        return response.status_code == 200
    
    # ==================== ORDER ENDPOINTS ====================
    def test_create_order(self):
        """Create an order"""
        self.print_section("ORDER MANAGEMENT")
        
        order_data = {
            "customer_id": "CUST_DEMO_001",
            "items": [
                {
                    "product_id": "prod_demo_001",
                    "sku": "DEMO_KURTA_M_BLU",
                    "quantity": 1,
                    "price": 699.99
                }
            ],
            "pincode": "110001",
            "warehouse_id": "W_DEMO",
            "total_amount": 699.99
        }
        
        response = self.session.post(
            f"{self.base_url}/api/orders",
            json=order_data
        )
        self.print_response(response, "Create Order")
        
        if response.status_code == 200:
            return response.json().get("order_id")
        return None
    
    def test_get_orders_by_status(self):
        """Get orders by status"""
        response = self.session.get(
            f"{self.base_url}/api/orders/status/pending?limit=5"
        )
        self.print_response(response, "Get Orders by Status")
        return response.status_code == 200
    
    # ==================== RECOMMENDATION ENDPOINTS ====================
    def test_text_recommendation(self):
        """Test text-based recommendations"""
        self.print_section("RECOMMENDATION ENGINE")
        
        query = {
            "text_input": "casual blue kurta for college",
            "pincode": "110001",
            "top_k": 5
        }
        
        response = self.session.post(
            f"{self.base_url}/api/recommendations",
            json=query
        )
        self.print_response(response, "Text-Based Recommendation")
        return response.status_code == 200
    
    def test_filtered_recommendation(self):
        """Test recommendations with filters"""
        query = {
            "text_input": "formal shirt",
            "pincode": "110002",
            "top_k": 3,
            "filters": {
                "min_price": 500,
                "max_price": 1500
            }
        }
        
        response = self.session.post(
            f"{self.base_url}/api/recommendations",
            json=query
        )
        self.print_response(response, "Filtered Recommendation")
        return response.status_code == 200
    
    # ==================== FORECAST ENDPOINTS ====================
    def test_create_forecast(self):
        """Create a demand forecast"""
        self.print_section("DEMAND FORECASTING")
        
        from datetime import datetime
        
        forecast_data = {
            "forecast_id": "FC_DEMO_001",
            "sku": "DEMO_KURTA_M_BLU",
            "product_id": "prod_demo_001",
            "pincode": "110001",
            "timestamp": datetime.utcnow().isoformat(),
            "forecast_hour": 14,
            "forecast_date": "2026-03-29",
            "predicted_demand": 8.5,
            "confidence_interval_lower": 6.5,
            "confidence_interval_upper": 10.5,
            "factors": {"weather": "sunny", "is_weekend": False}
        }
        
        response = self.session.post(
            f"{self.base_url}/api/forecasts",
            json=forecast_data
        )
        self.print_response(response, "Create Forecast")
        return response.status_code == 200
    
    def test_get_forecasts(self):
        """Get forecasts for SKU and pincode"""
        response = self.session.get(
            f"{self.base_url}/api/forecasts/DEMO_KURTA_M_BLU/110001?limit=10"
        )
        self.print_response(response, "Get Forecasts")
        return response.status_code == 200
    
    # ==================== AGENT ENDPOINTS ====================
    def test_trigger_optimization(self):
        """Trigger inventory optimization"""
        self.print_section("INVENTORY ORCHESTRATION (AGENT)")
        
        response = self.session.post(
            f"{self.base_url}/api/agent/trigger-optimization",
            params={"pincode": "110001"}
        )
        self.print_response(response, "Trigger Agent Optimization")
        return response.status_code == 200
    
    def test_get_agent_logs(self):
        """Get agent execution logs"""
        response = self.session.get(f"{self.base_url}/api/agent-logs?limit=5")
        self.print_response(response, "Get Agent Logs")
        return response.status_code == 200
    
    # ==================== ANALYTICS ENDPOINTS ====================
    def test_sla_metrics(self):
        """Get SLA metrics"""
        self.print_section("ANALYTICS & METRICS")
        
        response = self.session.get(f"{self.base_url}/api/stats/sla")
        self.print_response(response, "SLA Metrics")
        return response.status_code == 200
    
    # ==================== MAIN TEST RUNNER ====================
    def run_all_tests(self):
        """Run all API tests"""
        print("╔" + "═" * 58 + "╗")
        print("║" + " " * 20 + "ZINTOO API TEST SUITE" + " " * 15 + "║")
        print("╚" + "═" * 58 + "╝")
        
        print("\n📡 Connecting to server at:", self.base_url)
        
        # Check server is running
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=2)
            if response.status_code != 200:
                print("⚠ Server returned non-200 status")
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to server. Make sure FastAPI is running:")
            print("   python backend/main.py")
            return
        except Exception as e:
            print(f"⚠ Connection warning: {e}")
        
        # Run tests
        tests = [
            ("Health Check", self.test_health),
            ("API Info", self.test_root),
            ("Create Product", self.test_create_product),
            ("List Products", self.test_get_products),
            ("Add Inventory", self.test_add_inventory),
            ("Check Stock", self.test_check_stock),
            ("Create Order", self.test_create_order),
            ("Get Orders", self.test_get_orders_by_status),
            ("Text Recommendations", self.test_text_recommendation),
            ("Filtered Recommendations", self.test_filtered_recommendation),
            ("Create Forecast", self.test_create_forecast),
            ("Get Forecasts", self.test_get_forecasts),
            ("Trigger Agent Optimization", self.test_trigger_optimization),
            ("Get Agent Logs", self.test_get_agent_logs),
            ("Get SLA Metrics", self.test_sla_metrics),
        ]
        
        results = {}
        for test_name, test_func in tests:
            try:
                result = test_func()
                results[test_name] = "✓ PASS" if result else "⚠ WARN"
            except Exception as e:
                print(f"\n❌ Error in {test_name}: {e}")
                results[test_name] = "✗ FAIL"
            
            time.sleep(0.5)  # Rate limiting
        
        # Summary
        self.print_section("TEST SUMMARY")
        passed = sum(1 for v in results.values() if "PASS" in v)
        total = len(results)
        
        for test_name, result in results.items():
            print(f"  {result} - {test_name}")
        
        print(f"\n  Total: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n✅ All tests passed! Zintoo backend is fully operational.")
        else:
            print(f"\n⚠ {total - passed} tests failed. Check the logs above.")


if __name__ == "__main__":
    tester = ZintooAPITester()
    tester.run_all_tests()
