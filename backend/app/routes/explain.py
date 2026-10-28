from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..models.db import Prediction, get_session
from ..models.schemas import ExplainRequest, ExplainResponse
from ..services.explainer import explain as run_explain

router = APIRouter()


@router.post("/explain", response_model=ExplainResponse)
def explain(req: ExplainRequest, db: Session = Depends(get_session)):
    row = db.get(Prediction, req.prediction_id)
    if row is None:
        raise HTTPException(status_code=404, detail="prediction_id not found")

    gene_expression = json.loads(row.gene_expression_json)
    result = run_explain(gene_expression)
    return ExplainResponse(**result)
