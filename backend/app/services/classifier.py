from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np

ARTIFACTS_DIR = Path(__file__).resolve().parent.parent / "artifacts"

CONFIDENCE_HIGH = 0.85
CONFIDENCE_MODERATE = 0.65

# How far (in training standard deviations) a *present* gene's raw value
# can sit from the training mean before it stops looking like it came from
# the same assay (log2-scale, quantile-normalized microarray intensities).
UNUSUAL_SD_THRESHOLD = 4.0
UNUSUAL_FRACTION_THRESHOLD = 0.5


@lru_cache(maxsize=1)
def load_model():
    model = joblib.load(ARTIFACTS_DIR / "best_model.joblib")
    scaler = joblib.load(ARTIFACTS_DIR / "scaler.joblib")
    with open(ARTIFACTS_DIR / "selected_genes.json") as f:
        genes = json.load(f)
    with open(ARTIFACTS_DIR / "model_info.json") as f:
        info = json.load(f)
    return model, scaler, genes, info


def vectorize(gene_expression: dict[str, float], genes: list[str], scaler) -> tuple[np.ndarray, int, np.ndarray]:
    """Builds the feature vector in the model's expected gene order.
    Missing genes are imputed with the scaler's training-mean for that
    gene, so after scaler.transform() they land at 0 in standardized
    space — "no information" — rather than an extreme value. (Imputing
    the raw value as 0 instead, as this used to do, becomes a large
    negative z-score once scaled: training's raw log2 scale has no zero
    near it, so that silently told the model "very low expression" for
    every gene the caller didn't send, instead of "unknown".)"""
    present_mask = np.array([g in gene_expression for g in genes])
    values = np.array(
        [gene_expression[g] if present else scaler.mean_[i] for i, (g, present) in enumerate(zip(genes, present_mask))]
    ).reshape(1, -1)
    n_present = int(present_mask.sum())
    return values, n_present, present_mask


def input_quality_check(X_raw: np.ndarray, present_mask: np.ndarray, scaler) -> tuple[str, str | None]:
    """Flags input that doesn't look like it's on the training scale (e.g.
    raw RNA-seq counts, TPM, or a different platform's units uploaded by
    mistake) instead of silently returning a confident-looking prediction
    on meaningless input. Only present genes are checked — imputed ones
    are set to the training mean by construction and would never trip
    this, which is the point."""
    if not present_mask.any():
        return "typical", None
    z = (X_raw[0] - scaler.mean_) / scaler.scale_
    present_z = z[present_mask]
    frac_unusual = float(np.mean(np.abs(present_z) > UNUSUAL_SD_THRESHOLD))
    if frac_unusual > UNUSUAL_FRACTION_THRESHOLD:
        return "unusual", (
            "These values look different from the kind of data this model was trained on "
            "(log2-scale, quantile-normalized microarray intensities). Check with your lab "
            "about the test type before trusting this result."
        )
    return "typical", None


def predict(gene_expression: dict[str, float]) -> dict:
    model, scaler, genes, _ = load_model()
    X_raw, n_present, present_mask = vectorize(gene_expression, genes, scaler)
    X = scaler.transform(X_raw)

    proba = model.predict_proba(X)[0]
    # class order follows the model's fit order: 0=Healthy, 1=SLE
    p_healthy, p_sle = float(proba[0]), float(proba[1])
    prediction = "SLE" if p_sle >= 0.5 else "Healthy"
    top_p = max(p_sle, p_healthy)
    confidence = "high" if top_p > CONFIDENCE_HIGH else "moderate" if top_p > CONFIDENCE_MODERATE else "low"
    quality, quality_note = input_quality_check(X_raw, present_mask, scaler)

    return {
        "prediction": prediction,
        "probability": {"SLE": round(p_sle, 4), "Healthy": round(p_healthy, 4)},
        "confidence": confidence,
        "genes_used": n_present,
        "genes_expected": len(genes),
        "input_quality": quality,
        "input_quality_note": quality_note,
    }
