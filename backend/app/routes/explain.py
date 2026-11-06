from __future__ import annotations

from fastapi import APIRouter

from ..models.schemas import ExplainRequest, ExplainResponse
from ..services.explainer import explain as run_explain

router = APIRouter()


@router.post("/explain", response_model=ExplainResponse)
def explain(req: ExplainRequest):
    result = run_explain(req.gene_expression)
    return ExplainResponse(**result)
