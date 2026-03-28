from __future__ import annotations

from fastapi import FastAPI

from app.api.routes.forecast import router as forecast_router
from app.api.routes.orchestrate import router as orchestrate_router
from app.api.routes.recommend import router as recommend_router
from app.api.routes.simulate import router as simulate_router
from app.api.main import app


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Fashion Intelligence Platform",
        version="1.0.0",
        description="Multimodal recommendation, demand forecasting, and inventory orchestration APIs.",
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(recommend_router, prefix="/recommend", tags=["recommend"])
    app.include_router(forecast_router, prefix="/forecast", tags=["forecast"])
    app.include_router(orchestrate_router, prefix="/inventory", tags=["inventory"])
    app.include_router(simulate_router, prefix="/simulate", tags=["simulate"])

    return app


app = create_app()