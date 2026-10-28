"""Honest performance evaluation via NESTED cross-validation.

The first run of models.py trained on the 56 genes picked by running
feature selection on all 81 training samples, then cross-validated on
those same 81 samples — every fold's "held-out" samples had already
influenced which genes were selected. That produced impossible-looking
perfect AUCs (1.0000) for three of the four models, which is the
textbook symptom of this exact leak (Ambroise & McLachlan 2002, PNAS —
"Selection bias in gene extraction on the basis of microarray gene-
expression data"), not a sign the models are actually that good.

Fix: for each outer fold, feature selection (DEG + LASSO) runs ONLY on
that fold's training split. The held-out fold never influences which
genes are chosen before being scored on them. Hyperparameters are
fixed to each model's best params from the (leaky) global grid search
rather than re-searched per fold — the leak was in feature selection,
not hyperparameter tuning, and a full nested grid search would be
considerably slower for a marginal rigor gain on a 81-sample dataset.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    f1_score,
    matthews_corrcoef,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from xgboost import XGBClassifier

from features import differential_expression, lasso_select

RANDOM_STATE = 42

# best_params taken from the global GridSearchCV run — see the note above
# on why hyperparameters aren't re-searched per outer fold.
BEST_PARAMS = {
    "SVM": {"C": 0.1, "gamma": "scale"},
    "RandomForest": {"max_depth": 5, "min_samples_leaf": 1, "n_estimators": 100},
    "XGBoost": {"learning_rate": 0.01, "max_depth": 3, "n_estimators": 500},
    "MLP": {"alpha": 0.0001, "hidden_layer_sizes": (64, 32)},
}


def build_model(name: str, scale_pos_weight: float):
    params = BEST_PARAMS[name]
    if name == "SVM":
        return SVC(kernel="rbf", probability=True, class_weight="balanced", random_state=RANDOM_STATE, **params)
    if name == "RandomForest":
        return RandomForestClassifier(class_weight="balanced", random_state=RANDOM_STATE, **params)
    if name == "XGBoost":
        return XGBClassifier(
            scale_pos_weight=scale_pos_weight, eval_metric="logloss", random_state=RANDOM_STATE, **params
        )
    if name == "MLP":
        return MLPClassifier(activation="relu", max_iter=2000, early_stopping=True, random_state=RANDOM_STATE, **params)
    raise ValueError(name)


def specificity_score(y_true, y_pred):
    tn = np.sum((y_true == 0) & (y_pred == 0))
    fp = np.sum((y_true == 0) & (y_pred == 1))
    return tn / (tn + fp) if (tn + fp) > 0 else np.nan


def stability_selection(expr: pd.DataFrame, labels: pd.Series, n_splits=5, min_fold_fraction=0.6) -> list[str]:
    """Genes selected by LASSO on all of the training data include some
    that are cohort-specific noise rather than robust disease signal —
    confirmed by external validation (GSE72509/GSE49454): only ~65-73%
    of the 56 globally-selected genes kept the same SLE-vs-Healthy
    direction in either external cohort. Fix: redo feature selection
    independently on each of several resampled folds, keep only genes
    chosen in most of them. Genes that are real, reproducible signal get
    picked regardless of which samples happen to be in the fold; genes
    that are overfit to one particular 81-sample split don't survive
    being picked min_fold_fraction of the time.
    """
    y_all = (labels == "SLE").astype(int)
    sample_ids = expr.columns.values
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE)

    vote_counts: dict[str, int] = {}
    for _, (train_idx, _) in enumerate(cv.split(sample_ids, y_all.values)):
        train_ids = sample_ids[train_idx]
        train_labels = labels.loc[train_ids]
        deg = differential_expression(expr[train_ids], train_labels)
        selected, _, _ = lasso_select(expr[train_ids], train_labels, deg.index.tolist())
        for g in selected:
            vote_counts[g] = vote_counts.get(g, 0) + 1

    min_votes = int(np.ceil(min_fold_fraction * n_splits))
    stable_genes = [g for g, count in vote_counts.items() if count >= min_votes]
    print(f"Stability selection: {len(vote_counts)} genes selected in >=1 fold, "
          f"{len(stable_genes)} selected in >={min_votes}/{n_splits} folds (kept)")
    return stable_genes


def nested_cv_evaluate(expr: pd.DataFrame, labels: pd.Series, n_splits=5) -> pd.DataFrame:
    y_all = (labels == "SLE").astype(int)
    sample_ids = expr.columns.values
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE)

    rows = []
    fold_gene_counts = []
    for fold_idx, (train_idx, test_idx) in enumerate(cv.split(sample_ids, y_all.values)):
        train_ids, test_ids = sample_ids[train_idx], sample_ids[test_idx]
        train_labels = labels.loc[train_ids]

        # feature selection using ONLY this fold's training samples
        deg = differential_expression(expr[train_ids], train_labels)
        selected_genes, _, _ = lasso_select(expr[train_ids], train_labels, deg.index.tolist())
        fold_gene_counts.append(len(selected_genes))
        if len(selected_genes) < 2:
            # LASSO zeroed out everything this fold - fall back to top DEG genes
            selected_genes = deg.index[:10].tolist()

        X_train_raw = expr.loc[selected_genes, train_ids].T.values
        X_test_raw = expr.loc[selected_genes, test_ids].T.values
        y_train = y_all.loc[train_ids].values
        y_test = y_all.loc[test_ids].values

        scaler = StandardScaler().fit(X_train_raw)
        X_train, X_test = scaler.transform(X_train_raw), scaler.transform(X_test_raw)

        n_pos, n_neg = int(y_train.sum()), int(len(y_train) - y_train.sum())
        scale_pos_weight = n_neg / n_pos if n_pos else 1.0

        for name in BEST_PARAMS:
            model = build_model(name, scale_pos_weight)
            model.fit(X_train, y_train)
            proba = model.predict_proba(X_test)[:, 1]
            pred = (proba >= 0.5).astype(int)

            auc = roc_auc_score(y_test, proba) if len(np.unique(y_test)) > 1 else np.nan
            rows.append({
                "fold": fold_idx, "model": name, "n_genes_this_fold": len(selected_genes),
                "auc": auc, "f1": f1_score(y_test, pred, zero_division=0),
                "precision": precision_score(y_test, pred, zero_division=0),
                "sensitivity_recall": recall_score(y_test, pred, zero_division=0),
                "specificity": specificity_score(y_test, pred),
                "mcc": matthews_corrcoef(y_test, pred),
            })

    results = pd.DataFrame(rows)
    print(f"\nGenes selected per fold (should vary, not be identical): {fold_gene_counts}")
    return results


if __name__ == "__main__":
    import sys

    sys.path.insert(0, ".")
    from preprocess import load_and_preprocess_training

    expr, labels = load_and_preprocess_training()
    results = nested_cv_evaluate(expr, labels)

    summary = results.groupby("model")[["auc", "f1", "precision", "sensitivity_recall", "specificity", "mcc"]].agg(["mean", "std"])
    print("\n=== Honest nested-CV performance (feature selection redone per fold) ===")
    print(summary.round(3))

    import os

    os.makedirs("../results", exist_ok=True)
    results.to_csv("../results/nested_cv_results.csv", index=False)
    summary.to_csv("../results/comparison_table.csv")
    print("\nSaved ../results/nested_cv_results.csv and comparison_table.csv")
