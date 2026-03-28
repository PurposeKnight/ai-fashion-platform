#!/usr/bin/env python3
"""
Entry point to run the AI Fashion Intelligence Platform with orchestration engine
"""
import uvicorn
import os
from app.api.main import app

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    
    print(f"\n{'='*60}")
    print("🚀 AI Fashion Intelligence Platform")
    print(f"Running on http://{host}:{port}")
    print(f"📚 API Docs: http://localhost:{port}/docs")
    print(f"{'='*60}\n")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=False
    )
