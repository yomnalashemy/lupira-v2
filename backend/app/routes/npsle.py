from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..models.schemas import NpsleRequest, NpsleResponse
from ..services.npsle_scorer import score_npsle

router = APIRouter()


@router.post("/npsle-score", response_model=NpsleResponse)
def npsle_score(req: NpsleRequest):
    try:
        result = score_npsle(
            syndromes=req.syndromes,
            sle_diagnosis_confirmed=req.sle_diagnosis_confirmed,
            temporal_relation=req.temporal_relation,
            confounding_factors=req.confounding_factors,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return NpsleResponse(**result)
