"""Unit tests for evaluate.py, using small synthetic expression data —
fast and network-free. Specifically guards against the feature-selection
leakage bug found during development: genes picked using the held-out
fold's own labels inflated CV AUC to an impossible 1.000 for 3 of 4
models before nested_cv_evaluate redid selection per fold."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import numpy as np
import pandas as pd
import pytest

from evaluate import nested_cv_evaluate, specificity_score, stability_selection


@pytest.fixture(scope="module")
def synthetic_expression():
    rng = np.random.default_rng(42)
    n_samples, n_genes = 40, 60
    samples = [f"s{i}" for i in range(n_samples)]
    genes = [f"gene{i}" for i in range(n_genes)]
    labels = pd.Series(["SLE"] * 28 + ["Healthy"] * 12, index=samples, name="label")

    data = rng.normal(8, 1.5, size=(n_genes, n_samples))
    # make the first 8 genes genuinely informative so feature selection
    # has real signal to find, not just noise
    sle_mask = (labels == "SLE").values
    data[:8, sle_mask] += 2.0

    expr = pd.DataFrame(data, index=genes, columns=samples)
    return expr, labels


def test_specificity_score_computes_correctly():
    y_true = np.array([0, 0, 0, 1, 1])
    y_pred = np.array([0, 0, 1, 1, 0])
    # 2 true negatives, 1 false positive -> specificity 2/3
    assert specificity_score(y_true, y_pred) == pytest.approx(2 / 3)


def test_specificity_score_handles_no_negatives():
    y_true = np.array([1, 1, 1])
    y_pred = np.array([1, 0, 1])
    assert np.isnan(specificity_score(y_true, y_pred))


def test_cv_returns_all_expected_metrics(synthetic_expression):
    expr, labels = synthetic_expression
    results = nested_cv_evaluate(expr, labels, n_splits=3)
    expected_cols = {"fold", "model", "n_genes_this_fold", "auc", "f1", "precision", "sensitivity_recall", "specificity", "mcc"}
    assert expected_cols.issubset(set(results.columns))
    assert set(results["model"]) == {"SVM", "RandomForest", "XGBoost", "MLP"}


def test_no_data_leakage_feature_selection_varies_per_fold(synthetic_expression):
    """The actual bug this guards against: feature selection run once
    on the full dataset, then cross-validated, produced identical gene
    counts (and impossible 1.000 AUC) every fold. Real per-fold
    resampling should select a genuinely different number of genes
    fold to fold, not the same number every time."""
    expr, labels = synthetic_expression
    results = nested_cv_evaluate(expr, labels, n_splits=3)
    gene_counts_per_fold = results.groupby("fold")["n_genes_this_fold"].first()
    assert len(set(gene_counts_per_fold)) > 1, "feature selection should vary across folds, not be identical"


def test_metrics_within_valid_ranges(synthetic_expression):
    expr, labels = synthetic_expression
    results = nested_cv_evaluate(expr, labels, n_splits=3)
    assert results["auc"].dropna().between(0, 1).all()
    assert results["f1"].between(0, 1).all()
    assert results["mcc"].between(-1, 1).all()


def test_stability_selection_only_keeps_genes_chosen_in_most_folds(synthetic_expression):
    expr, labels = synthetic_expression
    stable_genes = stability_selection(expr, labels, n_splits=5, min_fold_fraction=0.6)
    # the 8 genes engineered to carry real signal should dominate the
    # stable set more than arbitrary noise genes would
    informative_genes = {f"gene{i}" for i in range(8)}
    assert len(set(stable_genes) & informative_genes) >= 1
