from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    gene_expression: dict[str, float] = Field(..., description="gene symbol -> expression value")
    patient_id: str | None = None


class PredictResponse(BaseModel):
    prediction: Literal["SLE", "Healthy"]
    probability: dict[str, float]
    confidence: Literal["high", "moderate", "low"]
    model_used: str
    prediction_id: str
    timestamp: datetime
    genes_used: int
    genes_expected: int
    # echoed back so the client can request /explain without the server
    # needing to have persisted this prediction — see ExplainRequest
    gene_expression: dict[str, float]


class ExplainRequest(BaseModel):
    # the client already has this from PredictResponse.gene_expression —
    # sending it back directly means /explain has no dependency on the
    # prediction row still existing server-side (SQLite on Render's free
    # tier is wiped on every spin-down, so a lookup-by-id would 404 for
    # any prediction made before the last idle restart)
    gene_expression: dict[str, float]


class ShapContribution(BaseModel):
    gene: str
    value: float
    expression: float
    direction: Literal["risk", "protective"]


class ExplainResponse(BaseModel):
    shap_values: list[ShapContribution]
    base_value: float
    top_genes_count: int


class NpsleRequest(BaseModel):
    syndromes: list[str]
    sle_diagnosis_confirmed: bool
    temporal_relation: Literal["within_3_months", "within_12_months", "over_12_months", "unknown"] = "unknown"
    confounding_factors: list[str] = Field(default_factory=list)


class MatchedSyndrome(BaseModel):
    name: str
    category: Literal["central", "peripheral"]
    weight: int
    attribution: Literal["definitely_sle", "possibly_sle", "likely_non_sle"]


class NpsleResponse(BaseModel):
    risk_score: float
    risk_category: Literal["Low", "Moderate", "High", "Critical"]
    matched_syndromes: list[MatchedSyndrome]
    note: str


class HealthResponse(BaseModel):
    status: Literal["ok"]
    model_loaded: bool
    model_name: str
    feature_count: int


class ModelInfoResponse(BaseModel):
    model_type: str
    training_dataset: str
    training_n_samples: int
    validation_datasets: list[str]
    metrics: dict
    n_features: int
    top_features: list[str]
    required_genes: list[str]
    notes: str
