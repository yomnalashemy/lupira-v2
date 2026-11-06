from __future__ import annotations

import json
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..models.db import Prediction, get_session
from ..models.schemas import PredictRequest, PredictResponse
from ..services.classifier import predict as run_prediction

router = APIRouter()


@router.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest, db: Session = Depends(get_session)):
    result = run_prediction(req.gene_expression)

    row = Prediction(
        patient_id=req.patient_id,
        prediction=result["prediction"],
        probability_sle=result["probability"]["SLE"],
        confidence=result["confidence"],
        gene_expression_json=json.dumps(req.gene_expression),
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    return PredictResponse(
        prediction=result["prediction"],
        probability=result["probability"],
        confidence=result["confidence"],
        model_used="SVM",
        prediction_id=row.id,
        timestamp=row.created_at or datetime.utcnow(),
        genes_used=result["genes_used"],
        genes_expected=result["genes_expected"],
        gene_expression=req.gene_expression,
    )
