"""Export the final model, scaler, gene list, and real evaluation metrics
for the backend to load. SVM is the shipped model — the most consistent
performer across both external validation sets (0.843 AUC on GSE72509,
0.768 on GSE49454), not just the best internal-CV score."""
from __future__ import annotations

import json
import os

import joblib
import numpy as np
import pandas as pd
import shap

from evaluate import nested_cv_evaluate
from external_data import load_gse49454, load_gse72509
from external_validate import score_external, train_final_models
from preprocess import load_and_preprocess_training

BEST_MODEL_NAME = "SVM"
ARTIFACTS_DIR = "../../backend/app/artifacts"


def main():
    os.makedirs(ARTIFACTS_DIR, exist_ok=True)

    print("Loading and preprocessing training data...")
    expr, labels = load_and_preprocess_training()

    print("Training final models (stability-selected genes, fit on all training data)...")
    models, selected_genes, scaler = train_final_models(expr, labels)

    print("Running nested CV for honest internal metrics...")
    cv_results = nested_cv_evaluate(expr, labels)
    cv_summary = cv_results.groupby("model")[["auc", "f1", "sensitivity_recall", "specificity", "mcc"]].mean()

    print("Scoring external validation sets...")
    expr72509, labels72509 = load_gse72509()
    expr49454, labels49454 = load_gse49454()
    ext_results = pd.concat([
        score_external(models, selected_genes, scaler, expr72509, labels72509, "GSE72509"),
        score_external(models, selected_genes, scaler, expr49454, labels49454, "GSE49454"),
    ], ignore_index=True)

    best_model = models[BEST_MODEL_NAME]
    joblib.dump(best_model, f"{ARTIFACTS_DIR}/best_model.joblib")
    joblib.dump(scaler, f"{ARTIFACTS_DIR}/scaler.joblib")
    with open(f"{ARTIFACTS_DIR}/selected_genes.json", "w") as f:
        json.dump(selected_genes, f, indent=2)

    # SHAP background sample — saved once here so the backend's
    # KernelExplainer doesn't need GEOparse/network access at startup
    # just to get a reference distribution
    X_raw = expr.loc[selected_genes].T.values
    X_scaled = scaler.transform(X_raw)
    background = shap.sample(X_scaled, min(30, len(X_scaled)), random_state=42)
    joblib.dump(np.asarray(background), f"{ARTIFACTS_DIR}/shap_background.joblib")

    model_row = cv_summary.loc[BEST_MODEL_NAME]
    ext_for_model = ext_results[ext_results["model"] == BEST_MODEL_NAME]
    model_info = {
        "model_type": BEST_MODEL_NAME,
        "training_dataset": "GSE50772",
        "training_n_samples": int(expr.shape[1]),
        "validation_datasets": ext_for_model["dataset"].tolist(),
        "metrics": {
            "cv_auc": round(float(model_row["auc"]), 4),
            "cv_f1": round(float(model_row["f1"]), 4),
            "cv_sensitivity": round(float(model_row["sensitivity_recall"]), 4),
            "cv_specificity": round(float(model_row["specificity"]), 4),
            "external_auc_by_dataset": {
                row["dataset"]: round(float(row["auc"]), 4) for _, row in ext_for_model.iterrows()
            },
        },
        "n_features": len(selected_genes),
        "top_features": selected_genes[:10],
        "required_genes": selected_genes,
        "notes": (
            "Trained on GSE50772 only (Affymetrix), not merged with GSE72509 "
            "(a different measurement technology, RNA-seq) — see project notes "
            "on cross-platform ComBat merging being scientifically invalid here. "
            "Both GSE72509 and GSE49454 are independent external validation sets, "
            "never used in feature selection or training."
        ),
    }
    with open(f"{ARTIFACTS_DIR}/model_info.json", "w") as f:
        json.dump(model_info, f, indent=2)

    print(f"\nExported to {ARTIFACTS_DIR}/:")
    print(f"  best_model.joblib ({BEST_MODEL_NAME})")
    print("  scaler.joblib")
    print(f"  selected_genes.json ({len(selected_genes)} genes)")
    print("  model_info.json")
    print(json.dumps(model_info, indent=2))


if __name__ == "__main__":
    main()
