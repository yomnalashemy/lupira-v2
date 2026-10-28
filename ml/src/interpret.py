"""SHAP interpretability for the final model (SVM — the most consistent
performer across both external validation sets: 0.843 AUC on GSE72509,
0.768 on GSE49454)."""
from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap

from evaluate import build_model
from external_validate import train_final_models
from preprocess import load_and_preprocess_training

BEST_MODEL_NAME = "SVM"


def compute_shap(expr: pd.DataFrame, labels: pd.Series):
    models, selected_genes, scaler = train_final_models(expr, labels)
    model = models[BEST_MODEL_NAME]

    X_raw = expr.loc[selected_genes].T.values
    X = scaler.transform(X_raw)
    sample_ids = expr.columns.tolist()

    # KernelExplainer (SVM has no tree structure to exploit) — background
    # set capped at 30 samples per the spec's pattern, training set is
    # only 81 samples so this is most of it anyway
    background = shap.sample(X, min(30, len(X)), random_state=42)
    explainer = shap.KernelExplainer(model.predict_proba, background)
    shap_values = explainer.shap_values(X, nsamples=100)

    # shap_values shape depends on sklearn/shap version — normalize to
    # the SLE-class (positive class) contributions, 2D (samples x genes)
    if isinstance(shap_values, list):
        sle_shap = shap_values[1]
    elif shap_values.ndim == 3:
        sle_shap = shap_values[:, :, 1]
    else:
        sle_shap = shap_values

    return {
        "shap_values": sle_shap,
        "base_value": explainer.expected_value[1] if hasattr(explainer.expected_value, "__len__") else explainer.expected_value,
        "genes": selected_genes,
        "sample_ids": sample_ids,
        "X_raw": X_raw,
        "model": model,
        "scaler": scaler,
    }


def save_summary_plots(result: dict, outdir="../results"):
    shap_values, genes = result["shap_values"], result["genes"]

    plt.figure()
    shap.summary_plot(shap_values, features=result["X_raw"], feature_names=genes, show=False, max_display=20)
    plt.tight_layout()
    plt.savefig(f"{outdir}/shap_summary_beeswarm.png", dpi=120)
    plt.close()

    mean_abs = np.abs(shap_values).mean(axis=0)
    order = np.argsort(mean_abs)[::-1][:20]
    plt.figure(figsize=(7, 6))
    plt.barh([genes[i] for i in order][::-1], mean_abs[order][::-1])
    plt.xlabel("mean |SHAP value|")
    plt.title("Top 20 genes by mean absolute SHAP (SVM)")
    plt.tight_layout()
    plt.savefig(f"{outdir}/shap_bar.png", dpi=120)
    plt.close()

    print(f"Saved {outdir}/shap_summary_beeswarm.png and {outdir}/shap_bar.png")
    return genes[int(np.argmax(mean_abs))]


if __name__ == "__main__":
    import os

    expr, labels = load_and_preprocess_training()
    result = compute_shap(expr, labels)
    os.makedirs("../results", exist_ok=True)
    top_gene = save_summary_plots(result)
    print(f"Top gene by mean |SHAP|: {top_gene}")

    # one real per-prediction waterfall, for the API's /explain response shape
    idx = 0
    print(f"\nExample per-prediction explanation for sample {result['sample_ids'][idx]}:")
    print(f"  base_value: {result['base_value']:.4f}")
    contribs = sorted(zip(result["genes"], result["shap_values"][idx], result["X_raw"][idx]), key=lambda t: -abs(t[1]))
    for gene, val, expr_val in contribs[:10]:
        direction = "risk" if val > 0 else "protective"
        print(f"  {gene}: shap={val:+.4f} expr={expr_val:.3f} ({direction})")
