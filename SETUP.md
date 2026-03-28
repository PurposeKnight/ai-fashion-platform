# SETUP INSTRUCTIONS - Zintoo Backend

## Prerequisites

- Python 3.9 or higher
- MongoDB (local or cloud)
- Git (optional, for version control)

## Step-by-Step Installation

### 1. Install Python Dependencies

```powershell
cd zintoo
pip install -r requirements.txt
```

This installs all required packages:
- FastAPI, Uvicorn (API server)
- PyMongo (MongoDB client)
- Torch, Transformers (ML)
- NumPy, Pandas, Scikit-learn (Data science)
- LangChain (Agent orchestration)

**Installation time:** ~5-10 minutes

### 2. Configure MongoDB

#### Option A: Local MongoDB (Recommended for Development)

1. **Install MongoDB Community Edition**
   - Windows: https://docs.mongodb.com/manual/tutorial/install-mongodb-on-windows/
   - Extract to `C:\mongodb` (or your preferred location)

2. **Create data directory**
   ```powershell
   mkdir C:\data\db
   ```

3. **Start MongoDB server**
   ```powershell
   C:\mongodb\bin\mongod.exe --dbpath "C:\data\db"
   ```
   
   Keep this terminal open - MongoDB runs in the foreground.

#### Option B: MongoDB Atlas (Cloud)

1. Create account: https://www.mongodb.com/cloud/atlas
2. Create cluster and get connection string
3. Update `.env`:
   ```ini
   MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/zintoo_db?retryWrites=true&w=majority
   ```

### 3. Generate Synthetic Data

```powershell
cd data
python generate_data.py
```

**Output:**
- ✓ Created 20 products
- ✓ Created ~100 inventory records
- ✓ Created 50 orders
- ✓ Created 336+ forecasts

**Time:** ~30 seconds

### 4. Start the FastAPI Server

```powershell
cd backend
python main.py
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

**Server is ready!**

---

## Verify Installation

### Test 1: Health Check
```powershell
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy", "timestamp": "2026-03-28T...", "service": "Zintoo API"}
```

### Test 2: API Documentation
Open in browser: http://localhost:8000/docs

You should see Swagger UI with all endpoints.

### Test 3: Run Full Test Suite
```powershell
python test_api.py
```

Expected output: `✓ PASS` for all 15 tests

### Test 4: Generate Evaluation Report
```powershell
python generate_report.py
```

This generates a comprehensive evaluation report with metrics.

---

## Quick Usage Examples

### Create a Product
```powershell
$body = @{
    product_id = "test_001"
    sku = "TEST_KURTA_M"
    name = "Test Kurta"
    category = "casual"
    description = "Test product"
    price = 599.99
    image_url = "http://example.com/img.jpg"
    color = "blue"
    size = "M"
    material = "cotton"
    brand = "Zintoo"
} | ConvertTo-Json

curl -X POST http://localhost:8000/api/products `
  -H "Content-Type: application/json" `
  -d $body
```

### Get Recommendations
```powershell
$query = @{
    text_input = "casual blue kurta"
    pincode = "110001"
    top_k = 5
} | ConvertTo-Json

curl -X POST http://localhost:8000/api/recommendations `
  -H "Content-Type: application/json" `
  -d $query
```

### Trigger Agent Optimization
```powershell
curl -X POST "http://localhost:8000/api/agent/trigger-optimization?pincode=110001"
```

---

## Troubleshooting

### MongoDB Connection Error
```
❌ MongoDB connection failed
```

**Solution:**
1. Ensure MongoDB server is running
2. Check `MONGODB_URI` in `.env`
3. Verify network connectivity
4. Check firewall settings

### Port Already in Use
```
Address already in use
```

**Solution:**
```powershell
# Change port in .env
PORT=8001

# Or kill existing process
Get-Process python | Where-Object {$_.CommandLine -like "*main.py*"} | Stop-Process
```

### Module Not Found
```
ModuleNotFoundError: No module named 'pymongo'
```

**Solution:**
```powershell
pip install --upgrade -r requirements.txt
```

### CORS Errors
The API has CORS enabled for all origins. If you still get CORS errors:
1. Clear browser cache
2. Try incognito/private mode
3. Check browser console for details

---

## File Descriptions

| File | Purpose |
|------|---------|
| `main.py` | FastAPI application with 18+ endpoints |
| `models.py` | Pydantic data models and MongoDB schemas |
| `database.py` | MongoDB connection and CRUD operations |
| `recommender.py` | Multimodal recommendation engine |
| `forecaster.py` | Demand forecasting module |
| `agent.py` | Inventory orchestration agent |
| `evaluator.py` | Metrics and evaluation framework |
| `requirements.txt` | Python package dependencies |
| `.env` | Configuration file |
| `README.md` | Full documentation |
| `generate_data.py` | Synthetic data generator |
| `test_api.py` | API testing suite |
| `generate_report.py` | Evaluation report generator |

---

## Environment Variables

```ini
# Database (required)
MONGODB_URI=mongodb://localhost:27017
DB_NAME=zintoo_db

# Server (optional)
PORT=8000
HOST=0.0.0.0
DEBUG=True

# Agent (optional)
AGENT_ENABLED=True
FORECAST_CHECK_INTERVAL_MINUTES=30
OPTIMIZATION_TRIGGER_THRESHOLD=0.7

# ML Models (optional)
CLIP_MODEL=openai/clip-vit-base-patch32
DEVICE=cpu
```

---

## Database Collections

Automatically created on first run:

1. **products** - Product catalog
2. **inventory** - Warehouse stock levels
3. **demand_forecasts** - Predicted demand
4. **orders** - Customer orders
5. **reallocations** - Stock movements
6. **agent_logs** - Agent execution traces

View data in MongoDB Compass or CLI:
```powershell
# Connect to MongoDB
mongo

# Switch to database
use zintoo_db

# View collections
show collections

# Check documents
db.products.find().pretty()
```

---

## Performance Tips

### For Development
- Use local MongoDB for faster access
- Keep `DEBUG=True` for better error messages
- Use VS Code with Python extension

### For Production
- Use MongoDB Atlas or self-managed cluster
- Set `DEBUG=False`
- Implement caching (Redis)
- Add rate limiting
- Enable authentication

---

## Common Commands

```powershell
# Start everything
python quickstart.py

# Just start server
python backend/main.py

# Generate data only
python data/generate_data.py

# Run tests
python test_api.py

# Generate report
python generate_report.py

# Clean synthetic data (optional)
# (Requires mongosh or MongoDB Compass)
# db.products.deleteMany({})
# db.inventory.deleteMany({})
# etc.
```

---

## Architecture Overview

```
┌─────────────────────────┐
│    FastAPI Server       │  ← HTTP/REST API
├─────────────────────────┤
│  Recommender Engine     │  ← Text/Image matching
│  Forecaster Module      │  ← Time-series prediction
│  Inventory Agent        │  ← Autonomous decisions
├─────────────────────────┤
│    Evaluator Module     │  ← Metrics & reporting
├─────────────────────────┤
│    Database Layer       │  ← MongoDB operations
├─────────────────────────┤
│   MongoDB Database      │  ← Document storage
└─────────────────────────┘
```

---

## API Documentation

After starting server, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## Next Steps

1. ✅ Install dependencies
2. ✅ Start MongoDB
3. ✅ Generate data
4. ✅ Start server
5. ✅ Test API
6. 🔄 Explore endpoints
7. 🔄 Experiment with modules
8. 🔄 Deploy to production

---

## Support & Debugging

### Enable Detailed Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check MongoDB Connection
```powershell
python -c "from backend.database import get_db; db = get_db(); print('Connected!' if db.client else 'Failed')"
```

### Verify API Routes
```powershell
curl http://localhost:8000/
```

---

## Additional Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **MongoDB Docs**: https://docs.mongodb.com/
- **Python Guide**: https://docs.python.org/3/
- **Project README**: See README.md

---

**Installation Complete! 🎉**

Your Zintoo backend is ready to use. 

Next: Open http://localhost:8000/docs in your browser to explore the API!

---

Last updated: March 28, 2026
Version: 1.0.0
