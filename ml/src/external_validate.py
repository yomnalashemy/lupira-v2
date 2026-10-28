"""External validation: train on all of GSE50772 (training data), score
on GSE72509 and GSE49454 — real test of generalization, since neither
external set contributed to feature selection or training at any point.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, matthews_corrcoef, precision_score, recall_score, roc_auc_score
from sklearn.preprocessing import StandardScaler

from evaluate import BEST_PARAMS, build_model, specificity_score, stability_selection
from external_data import load_gse49454, load_gse72509
from preprocess import load_and_preprocess_training


def train_final_models(expr: pd.DataFrame, labels: pd.Series):
    """Stability-selected genes (not a single global LASSO fit — see
    evaluate.stability_selection for why) + all 4 models, fit on ALL
    training samples."""
    selected_genes = stability_selection(expr, labels)

    X_raw = expr.loc[selected_genes].T.values
    y = (labels == "SLE").astype(int).values
    scaler = StandardScaler().fit(X_raw)
    X = scaler.transform(X_raw)

    n_pos, n_neg = int(y.sum()), int(len(y) - y.sum())
    scale_pos_weight = n_neg / n_pos

    models = {}
    for name in BEST_PARAMS:
        model = build_model(name, scale_pos_weight)
        model.fit(X, y)
        models[name] = model
    return models, selected_genes, scaler


def score_external(models: dict, selected_genes: list[str], scaler: StandardScaler, ext_expr: pd.DataFrame, ext_labels: pd.Series, dataset_name: str) -> pd.DataFrame:
    available = [g for g in selected_genes if g in ext_expr.index]
    missing = [g for g in selected_genes if g not in ext_expr.index]
    print(f"\n{dataset_name}: {len(available)}/{len(selected_genes)} selected genes present "
          f"({len(missing)} missing: {missing[:10]}{'...' if len(missing) > 10 else ''})")

    # genes missing from this platform are imputed as 0 (the z-scored
    # mean) rather than dropping the gene for every sample on all
    # platforms — the classifier still gets a value for every feature
    # it expects, at the cost of that one gene carrying no signal here
    X = pd.DataFrame(0.0, index=ext_expr.columns, columns=selected_genes)
    X.loc[:, available] = ext_expr.loc[available].T.values

    y = (ext_labels.loc[X.index] == "SLE").astype(int).values
    # external data is already self-z-scored per gene within its own
    # cohort (external_data.py) — that's the whole point, since its raw
    # scale isn't comparable to training's. Running it through the
    # TRAINING-fitted scaler on top of that was the actual bug: it
    # subtracted training's raw log2-intensity mean (~8-10) from values
    # that were already ~0, producing a near-constant large offset for
    # every sample regardless of label. The training scaler is for
    # training-scale input only; self-standardized external data goes
    # to the models directly.
    X_scaled = X.values

    rows = []
    for name, model in models.items():
        proba = model.predict_proba(X_scaled)[:, 1]
        pred = (proba >= 0.5).astype(int)
        rows.append({
            "dataset": dataset_name, "model": name,
            "genes_available": len(available), "genes_total": len(selected_genes),
            "auc": roc_auc_score(y, proba),
            "f1": f1_score(y, pred, zero_division=0),
            "precision": precision_score(y, pred, zero_division=0),
            "sensitivity_recall": recall_score(y, pred, zero_division=0),
            "specificity": specificity_score(y, pred),
            "mcc": matthews_corrcoef(y, pred),
        })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    print("Training final models on all of GSE50772...")
    expr, labels = load_and_preprocess_training()
    models, selected_genes, scaler = train_final_models(expr, labels)
    print(f"Final gene set: {len(selected_genes)} genes")

    print("\nLoading external validation sets...")
    expr72509, labels72509 = load_gse72509()
    expr49454, labels49454 = load_gse49454()

    results = pd.concat([
        score_external(models, selected_genes, scaler, expr72509, labels72509, "GSE72509 (RNA-seq)"),
        score_external(models, selected_genes, scaler, expr49454, labels49454, "GSE49454 (Illumina)"),
    ], ignore_index=True)

    print("\n=== External validation results ===")
    print(results.to_string(index=False))

    import os

    os.makedirs("../results", exist_ok=True)
    results.to_csv("../results/external_validation.csv", index=False)
    with open("../data/processed/final_selected_genes.json", "w") as f:
        json.dump(selected_genes, f, indent=2)
    print("\nSaved ../results/external_validation.csv")
