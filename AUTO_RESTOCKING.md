# AUTO-RESTOCKING SYSTEM

## Overview
The AI Fashion Platform now includes an **automated inventory restocking system** that continuously monitors stock levels and automatically triggers restock actions when items fall below a configurable threshold.

---

## How It Works

### 1. **Continuous Monitoring**
- Background scheduler runs every **5 minutes** (configurable)
- Scans all warehouse inventory across all SKUs
- Identifies items below the restock threshold (default: **20 units**)

### 2. **Automatic Restocking Triggers**
When low stock is detected:
- System generates restock transfer orders automatically
- Source warehouse: Main distribution hub (WH-Delhi-A)
- Target quantity: Aims to bring stock to ~50 units
- Action logged to history for audit trail

### 3. **Zero Manual Intervention**
- No manual triggers needed
- Runs 24/7 in the background
- Prevents stockouts automatically

---

## Configuration

### Restock Threshold
- **Current**: 20 units
- **API Endpoint**: `POST /inventory/auto-restock/update-threshold?threshold=<value>`
- Example: When stock < 20, auto-restock is triggered

### Check Interval
- **Current**: 5 minutes
- **API Endpoint**: `POST /inventory/auto-restock/update-interval?minutes=<value>`
- Can be adjusted based on inventory velocity

---

## API Endpoints

### 1. Get Auto-Restock Status
```
GET /inventory/auto-restock/status
Response:
{
  "system": {
    "running": true,
    "threshold": 20,
    "check_interval_minutes": 5,
    "recent_actions": 0
  },
  "message": "Auto-restocking system is monitoring inventory in real-time"
}
```

### 2. Get Restock History
```
GET /inventory/auto-restock/history?limit=50
Response:
{
  "total_actions": 45,
  "recent_actions": [
    {
      "timestamp": "2026-03-28T10:15:32.123456",
      "action_type": "auto_transfer",
      "sku_id": "KURTA_001_M_BLU",
      "warehouse_id": "WH-Mumbai-B",
      "current_stock": 8,
      "restock_quantity": 42,
      "target_level": 50,
      "priority": "high",
      "status": "completed"
    }
  ]
}
```

### 3. Manually Trigger Check
```
POST /inventory/auto-restock/trigger
Response:
{
  "success": true,
  "message": "Auto-restock check triggered successfully",
  "recent_actions": [...]
}
```

### 4. Update Restock Threshold
```
POST /inventory/auto-restock/update-threshold?threshold=30
Response:
{
  "success": true,
  "message": "Threshold updated from 20 to 30",
  "threshold": 30
}
```

### 5. Update Check Interval
```
POST /inventory/auto-restock/update-interval?minutes=10
Response:
{
  "success": true,
  "message": "Check interval updated from 5 to 10 minutes",
  "interval_minutes": 10
}
```

---

## System Behavior

### High Priority Items
- Stock < 10 units → **Priority: CRITICAL**
- Immediate transfer initiated

### Medium Priority Items
- Stock 10-20 units → **Priority: MEDIUM**
- Standard restock workflow

### Action Status Tracking
- `pending` - Queued for execution
- `completed` - Successfully restocked
- `failed` - Error during execution

---

## Frontend Integration

The frontend now includes:

1. **Auto-Restock Status Widget**
   - Shows system status: ✓ Running / Stopped
   - Current threshold settings
   - Recent action count

2. **Restock History View**
   - Lists recent automatic restocking actions
   - Timestamp, SKU, warehouse, quantities
   - Success/failure indicators

3. **Manual Trigger Button**
   - For on-demand inventory checks
   - Useful for testing or emergency situations

---

## Key Features

✓ **24/7 Monitoring** - Never misses low stock
✓ **Automatic Execution** - No manual intervention needed
✓ **Priority-Based** - Critical items handled first
✓ **Configurable** - Adjust thresholds and intervals
✓ **Audit Trail** - Full history of all actions
✓ **Real-Time** - Multi-warehouse coordination
✓ **Failure Handling** - Graceful error management

---

## Example Workflow

```
Time: 10:15 AM
1. Auto-restock scheduler triggers
2. Scans all 200 SKUs across 8 warehouses
3. Finds KURTA_001_M_BLU in WH-Mumbai-B has 8 units
4. Below threshold (20), so generates action:
   - Source: WH-Delhi-A (has 150+ units)
   - Destination: WH-Mumbai-B
   - Quantity: 42 units (to reach 50)
   - ETA: 12 hours
5. Transfer executed automatically
6. Stock updated: WH-Mumbai-B now has 50 units
7. Action logged to history
```

---

## Starting the System

The auto-restocking system starts automatically when the backend server launches:

```bash
cd ai-fashion-platform
python backend/main.py
```

In logs, you'll see:
```
INFO:     Auto-restocking system initialized
INFO:     [AUTO-RESTOCK] Auto-restocking system started (checks every 5 minutes, threshold: 20)
```

---

## Monitoring & Debugging

### Check System Status
```python
import requests
status = requests.get('http://localhost:8000/inventory/auto-restock/status').json()
print(f"Running: {status['system']['running']}")
print(f"Threshold: {status['system']['threshold']}")
```

### View Recent Actions
```python
import requests
history = requests.get('http://localhost:8000/inventory/auto-restock/history?limit=10').json()
for action in history['recent_actions']:
    print(f"{action['timestamp']}: {action['sku_id']} -> {action['current_stock']} ++ {action['restock_quantity']}")
```

---

## Benefits

1. **Prevents Stockouts** - Automatic restocking prevents lost sales due to out-of-stock
2. **Optimizes Inventory** - Maintains optimal stock levels across all warehouses
3. **Improves SLA** - Ensures fast fulfillment by keeping stock available
4. **Reduces Manual Work** - No need for manual inventory management
5. **Data-Driven** - Actions logged for analytics and optimization
6. **Scales Easily** - Works with any number of warehouses and SKUs

---

**System Status**: ✓ ACTIVE AND MONITORING
**Monitor via**: Frontend Dashboard or `/inventory/auto-restock/status` API
