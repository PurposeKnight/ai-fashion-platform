from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.api.schemas import RecommendationRequest, RecommendationResponse
from app.data.synthetic.catalogue import generate_catalogue
from app.data.synthetic.warehouses import generate_warehouses, generate_inventory
from app.recommender.pipeline import (
    recommend_by_image,
    recommend_by_text,
    recommend_multimodal,
)

router = APIRouter()

# Temporary in-memory synthetic data for route testing
_catalogue = generate_catalogue(300)
_warehouses = generate_warehouses(8)
_inventory = generate_inventory(_catalogue, _warehouses)


@router.post("/text", response_model=RecommendationResponse)
def recommend_text(request: RecommendationRequest) -> RecommendationResponse:
    result = recommend_by_text(
        request=request,
        catalogue=_catalogue,
        inventory=_inventory,
    )
    return RecommendationResponse(**result)


@router.post("/image", response_model=RecommendationResponse)
async def recommend_image(
    pincode: str,
    top_k: int = 5,
    image: UploadFile = File(...),
) -> RecommendationResponse:
    image_bytes = await image.read()

    request = RecommendationRequest(
        pincode=pincode,
        top_k=top_k,
        mode="image",
    )

    result = recommend_by_image(
        image_bytes=image_bytes,
        request=request,
        catalogue=_catalogue,
        inventory=_inventory,
    )
    return RecommendationResponse(**result)


@router.post("/multimodal", response_model=RecommendationResponse)
async def recommend_multimodal_route(
    text_query: str,
    pincode: str,
    top_k: int = 5,
    image: UploadFile = File(...),
) -> RecommendationResponse:
    image_bytes = await image.read()

    request = RecommendationRequest(
        text_query=text_query,
        pincode=pincode,
        top_k=top_k,
        mode="multimodal",
    )

    result = recommend_multimodal(
        request=request,
        image_bytes=image_bytes,
        catalogue=_catalogue,
        inventory=_inventory,
    )
    return RecommendationResponse(**result)