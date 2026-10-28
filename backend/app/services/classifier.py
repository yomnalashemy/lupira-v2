from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np

ARTIFACTS_DIR = Path(__file__).resolve().parent.parent / "artifacts"

CONFIDENCE_HIGH = 0.85
CONFIDENCE_MODERATE = 0.65


@lru_cache(maxsize=1)
def load_model():
    model = joblib.load(ARTIFACTS_DIR / "best_model.joblib")
    scaler = joblib.load(ARTIFACTS_DIR / "scaler.joblib")
    with open(ARTIFACTS_DIR / "selected_genes.json") as f:
        genes = json.load(f)
    with open(ARTIFACTS_DIR / "model_info.json") as f:
        info = json.load(f)
    return model, scaler, genes, info


def vectorize(gene_expression: dict[str, float], genes: list[str]) -> tuple[np.ndarray, int]:
    """Builds the feature vector in the model's expected gene order.
    Missing genes are imputed as 0 (the scaler's mean in standardized
    space) — same convention used during external validation."""
    values = np.array([gene_expression.get(g, 0.0) for g in genes]).reshape(1, -1)
    n_present = sum(1 for g in genes if g in gene_expression)
    return values, n_present


def predict(gene_expression: dict[str, float]) -> dict:
    model, scaler, genes, _ = load_model()
    X_raw, n_present = vectorize(gene_expression, genes)
    X = scaler.transform(X_raw)

    proba = model.predict_proba(X)[0]
    # class order follows the model's fit order: 0=Healthy, 1=SLE
    p_healthy, p_sle = float(proba[0]), float(proba[1])
    prediction = "SLE" if p_sle >= 0.5 else "Healthy"
    top_p = max(p_sle, p_healthy)
    confidence = "high" if top_p > CONFIDENCE_HIGH else "moderate" if top_p > CONFIDENCE_MODERATE else "low"

    return {
        "prediction": prediction,
        "probability": {"SLE": round(p_sle, 4), "Healthy": round(p_healthy, 4)},
        "confidence": confidence,
        "genes_used": n_present,
        "genes_expected": len(genes),
    }
