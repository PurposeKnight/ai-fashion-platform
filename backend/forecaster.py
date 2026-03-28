"""
Hyper-Local Demand Forecasting Module
Predicts hourly SKU-level demand per pincode with confidence intervals
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from sklearn.preprocessing import StandardScaler
from models import DemandForecast, DemandContext
from database import get_db
import uuid


class DemandForecaster:
    """Demand forecasting engine for hyper-local SKU-level predictions"""
    
    def __init__(self):
        self.db = get_db()
        self.scaler = StandardScaler()
        self.models = {}  # Cache for fitted models
    
    def get_historical_demand(self, sku: str, pincode: str, days_lookback: int = 30) -> List[DemandForecast]:
        """Retrieve historical demand data"""
        forecasts = self.db.get_forecasts(sku, pincode, limit=days_lookback * 24)
        return forecasts
    
    def create_time_features(self, timestamp: datetime) -> Dict[str, float]:
        """Create time-based features for demand prediction"""
        return {
            "hour_of_day": timestamp.hour,
            "day_of_week": timestamp.weekday(),
            "is_weekend": 1 if timestamp.weekday() >= 5 else 0,
            "day_of_month": timestamp.day,
            "month": timestamp.month,
            "quarter": (timestamp.month - 1) // 3 + 1
        }
    
    def extract_hourly_patterns(self, historical_data: List[DemandForecast]) -> Dict[int, Tuple[float, float]]:
        """
        Extract hourly demand patterns
        Returns mean and std for each hour of day
        """
        hourly_demands = {h: [] for h in range(24)}
        
        for forecast in historical_data:
            hourly_demands[forecast.forecast_hour].append(forecast.predicted_demand)
        
        hourly_stats = {}
        for hour, demands in hourly_demands.items():
            if demands:
                hourly_stats[hour] = (np.mean(demands), np.std(demands))
            else:
                hourly_stats[hour] = (0, 0)
        
        return hourly_stats
    
    def extract_weekly_patterns(self, historical_data: List[DemandForecast]) -> Dict[int, float]:
        """
        Extract weekly demand patterns
        Returns demand multiplier by day of week
        """
        day_demands = {d: [] for d in range(7)}
        
        for forecast in historical_data:
            forecast_dt = datetime.fromisoformat(forecast.forecast_date.replace('Z', '+00:00')) if 'T' not in forecast.forecast_date else datetime.fromisoformat(forecast.forecast_date)
            day_of_week = forecast_dt.weekday()
            day_demands[day_of_week].append(forecast.predicted_demand)
        
        avg_demand = np.mean([d for demands in day_demands.values() for d in demands]) if any(day_demands.values()) else 1
        
        weekly_multipliers = {}
        for day, demands in day_demands.items():
            if demands:
                weekly_multipliers[day] = np.mean(demands) / max(avg_demand, 0.1)
            else:
                weekly_multipliers[day] = 1.0
        
        return weekly_multipliers
    
    def predict_demand_simple(self, sku: str, pincode: str, forecast_hour: int, forecast_date: str) -> Tuple[float, float, float]:
        """
        Simple demand prediction using patterns
        Returns: predicted_demand, lower_bound, upper_bound
        """
        historical = self.get_historical_demand(sku, pincode, days_lookback=30)
        
        if not historical:
            # Default forecast if no history
            base_demand = 5.0
            std = 1.0
        else:
            hourly_patterns = self.extract_hourly_patterns(historical)
            weekly_patterns = self.extract_weekly_patterns(historical)
            
            # Get forecast date info
            try:
                forecast_dt = datetime.strptime(forecast_date, "%Y-%m-%d")
                day_of_week = forecast_dt.weekday()
            except:
                forecast_dt = datetime.utcnow()
                day_of_week = forecast_dt.weekday()
            
            # Base demand from hourly pattern
            base_demand, hour_std = hourly_patterns.get(forecast_hour, (5.0, 1.0))
            
            # Apply weekly multiplier
            weekly_mult = weekly_patterns.get(day_of_week, 1.0)
            base_demand = base_demand * weekly_mult
            
            # Add some randomness for variation
            std = hour_std * 1.2
        
        # Generate confidence intervals (95%)
        lower_bound = max(0, base_demand - 1.96 * std)
        upper_bound = base_demand + 1.96 * std
        
        return base_demand, lower_bound, upper_bound
    
    def forecast_for_sku_pincode(self, sku: str, pincode: str, hours_ahead: int = 48) -> List[DemandForecast]:
        """
        Generate demand forecasts for next N hours
        """
        forecasts = []
        current_time = datetime.utcnow()
        
        for hour_offset in range(0, hours_ahead, 1):
            forecast_time = current_time + timedelta(hours=hour_offset)
            forecast_hour = forecast_time.hour
            forecast_date = forecast_time.strftime("%Y-%m-%d")
            
            predicted, lower, upper = self.predict_demand_simple(sku, pincode, forecast_hour, forecast_date)
            
            forecast = DemandForecast(
                forecast_id=f"FC-{uuid.uuid4().hex[:8].upper()}",
                sku=sku,
                product_id=sku.split('_')[0],
                pincode=pincode,
                timestamp=forecast_time,
                forecast_hour=forecast_hour,
                forecast_date=forecast_date,
                predicted_demand=predicted,
                confidence_interval_lower=lower,
                confidence_interval_upper=upper,
                factors={
                    "method": "simple_pattern",
                    "hour_pattern": True,
                    "weekly_pattern": True,
                    "confidence": 0.95
                }
            )
            forecasts.append(forecast)
        
        return forecasts
    
    def forecast_for_pincode(self, pincode: str, skus: Optional[List[str]] = None, hours_ahead: int = 48) -> Dict[str, List[DemandForecast]]:
        """
        Generate forecasts for multiple SKUs in a pincode
        """
        if skus is None:
            # Get all SKUs available in this pincode
            inventory = self.db.get_inventory_by_pincode(pincode)
            skus = list(set(inv.sku for inv in inventory))
        
        all_forecasts = {}
        for sku in skus:
            all_forecasts[sku] = self.forecast_for_sku_pincode(sku, pincode, hours_ahead)
        
        return all_forecasts
    
    def evaluate_forecast_accuracy(self, sku: str, pincode: str, evaluation_days: int = 7) -> Dict[str, float]:
        """
        Evaluate forecast accuracy using historical data
        Returns MAPE, RMSE, MAE
        """
        historical = self.get_historical_demand(sku, pincode, days_lookback=evaluation_days)
        
        if len(historical) < 2:
            return {"mape": 0, "rmse": 0, "mae": 0, "samples": 0}
        
        # Convert to arrays
        actual = np.array([f.predicted_demand for f in historical])
        
        # Generate predictions for same periods
        predictions = []
        for forecast in historical:
            pred, _, _ = self.predict_demand_simple(sku, pincode, forecast.forecast_hour, forecast.forecast_date)
            predictions.append(pred)
        
        predictions = np.array(predictions)
        
        # Calculate metrics
        mape = np.mean(np.abs((actual - predictions) / (actual + 0.001))) * 100
        rmse = np.sqrt(np.mean((actual - predictions) ** 2))
        mae = np.mean(np.abs(actual - predictions))
        
        return {
            "mape": round(mape, 2),
            "rmse": round(rmse, 2),
            "mae": round(mae, 2),
            "samples": len(historical),
            "evaluation_period_days": evaluation_days
        }


def create_forecaster() -> DemandForecaster:
    """Factory function to create a demand forecaster"""
    return DemandForecaster()
