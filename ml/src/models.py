"""Train SVM, Random Forest, XGBoost, and MLP with GridSearchCV + 5-fold
stratified CV on the LASSO-selected gene set. All four are trained and
reported — not just the best one (spec section 9: honest reporting)."""
from __future__ import annotations

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC
from xgboost import XGBClassifier

RANDOM_STATE = 42


def build_grids(scale_pos_weight: float) -> dict:
    return {
        "SVM": (
            SVC(kernel="rbf", probability=True, class_weight="balanced", random_state=RANDOM_STATE),
            {"C": [0.1, 1, 10, 100], "gamma": ["scale", "auto", 0.01, 0.001]},
        ),
        "RandomForest": (
            RandomForestClassifier(class_weight="balanced", random_state=RANDOM_STATE),
            {"n_estimators": [100, 200, 500], "max_depth": [5, 10, 20, None], "min_samples_leaf": [1, 2, 5]},
        ),
        "XGBoost": (
            XGBClassifier(
                scale_pos_weight=scale_pos_weight, eval_metric="logloss",
                random_state=RANDOM_STATE, use_label_encoder=False,
            ),
            {"n_estimators": [100, 200, 500], "max_depth": [3, 5, 7], "learning_rate": [0.01, 0.1, 0.3]},
        ),
        "MLP": (
            MLPClassifier(
                activation="relu", max_iter=2000, early_stopping=True, random_state=RANDOM_STATE,
            ),
            {"hidden_layer_sizes": [(64, 32), (128, 64), (256, 128, 64)], "alpha": [0.0001, 0.001, 0.01]},
        ),
    }


def train_all(X: np.ndarray, y: np.ndarray) -> dict:
    """Returns {name: fitted GridSearchCV} for all four models."""
    n_pos = int(y.sum())
    n_neg = len(y) - n_pos
    scale_pos_weight = n_neg / n_pos

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    results = {}
    for name, (estimator, grid) in build_grids(scale_pos_weight).items():
        search = GridSearchCV(estimator, grid, cv=cv, scoring="roc_auc", n_jobs=-1)
        search.fit(X, y)
        results[name] = search
        print(f"{name}: best CV AUC={search.best_score_:.4f}, best params={search.best_params_}")
    return results


if __name__ == "__main__":
    import json
    import sys

    sys.path.insert(0, ".")
    from preprocess import load_and_preprocess_training

    expr, labels = load_and_preprocess_training()
    with open("../data/processed/selected_genes.json") as f:
        genes = json.load(f)

    X = expr.loc[genes].T.values
    y = (labels.loc[expr.columns] == "SLE").astype(int).values

    from sklearn.preprocessing import StandardScaler

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    results = train_all(X_scaled, y)

    best_name = max(results, key=lambda n: results[n].best_score_)
    print(f"\nBest model by CV AUC: {best_name} ({results[best_name].best_score_:.4f})")

    import os

    os.makedirs("../results", exist_ok=True)
    joblib.dump(results[best_name].best_estimator_, "../results/best_model.joblib")
    joblib.dump(scaler, "../results/scaler.joblib")
    print("Saved best_model.joblib and scaler.joblib")
