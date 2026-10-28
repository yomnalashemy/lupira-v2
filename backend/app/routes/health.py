from __future__ import annotations

from fastapi import APIRouter

from ..models.schemas import HealthResponse, ModelInfoResponse
from ..services.classifier import load_model

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health():
    model, _, genes, info = load_model()
    return HealthResponse(
        status="ok", model_loaded=model is not None, model_name=info["model_type"], feature_count=len(genes)
    )


@router.get("/model-info", response_model=ModelInfoResponse)
def model_info():
    _, _, _, info = load_model()
    return ModelInfoResponse(**info)
