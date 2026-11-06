from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import shap

from .classifier import load_model, vectorize

ARTIFACTS_DIR = Path(__file__).resolve().parent.parent / "artifacts"


@lru_cache(maxsize=1)
def get_explainer():
    model, _, _, _ = load_model()
    background = joblib.load(ARTIFACTS_DIR / "shap_background.joblib")
    return shap.KernelExplainer(model.predict_proba, background)


def explain(gene_expression: dict[str, float], top_n: int = 15) -> dict:
    _, scaler, genes, _ = load_model()
    explainer = get_explainer()

    X_raw, _, _ = vectorize(gene_expression, genes, scaler)
    X = scaler.transform(X_raw)

    shap_values = explainer.shap_values(X, nsamples=100, silent=True)
    if isinstance(shap_values, list):
        sle_shap = shap_values[1][0]
    elif np.asarray(shap_values).ndim == 3:
        sle_shap = np.asarray(shap_values)[0, :, 1]
    else:
        sle_shap = np.asarray(shap_values)[0]

    base_value = explainer.expected_value
    base_value = float(base_value[1]) if hasattr(base_value, "__len__") else float(base_value)

    contributions = sorted(
        zip(genes, sle_shap, X_raw[0]), key=lambda t: -abs(t[1])
    )[:top_n]

    return {
        "shap_values": [
            {
                "gene": gene,
                "value": round(float(val), 4),
                "expression": round(float(expr), 4),
                "direction": "risk" if val > 0 else "protective",
            }
            for gene, val, expr in contributions
        ],
        "base_value": round(base_value, 4),
        "top_genes_count": len(contributions),
    }
