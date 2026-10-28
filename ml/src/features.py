"""Two-stage feature selection: differential expression filtering, then
LASSO regularization on the surviving genes."""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LogisticRegressionCV
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.multitest import multipletests

# SLE is strongly female-predominant (real epidemiology, not a sampling
# artifact), which means Y-chromosome genes end up correlated with
# disease status by proxy for patient sex, not lupus biology — RPS4Y1,
# USP9Y, and EIF1AY showed up in an unfiltered LASSO run on this exact
# cohort, confirming the confound rather than being a hypothetical risk.
# Standard practice in published SLE expression-classifier work is to
# exclude sex-chromosome genes from the candidate pool before selection,
# so the model is learning disease signal, not sex. This is the stable,
# well-documented set of human Y-chromosome protein-coding genes.
Y_CHROMOSOME_GENES = {
    "SRY", "RPS4Y1", "RPS4Y2", "ZFY", "AMELY", "TBL1Y", "PCDH11Y", "TGIF2LY",
    "TSPY1", "TSPY2", "TSPY3", "TSPY4", "TSPY8", "AMELX", "USP9Y", "DDX3Y",
    "UTY", "TMSB4Y", "NLGN4Y", "KDM5D", "EIF1AY", "RPS4Y1P1", "XKRY", "XKRY2",
    "PRY", "PRY2", "HSFY1", "HSFY2", "RBMY1A1", "RBMY1B", "RBMY1D", "RBMY1E",
    "RBMY1F", "RBMY1J", "DAZ1", "DAZ2", "DAZ3", "DAZ4", "CDY1", "CDY1B",
    "CDY2A", "CDY2B", "BPY2", "BPY2B", "BPY2C", "VCY", "VCY1B", "SRY1",
    "ZFY-AS1", "TXLNGY", "RPS4Y1P2",
}

# The single most notorious sex-confound gene in expression studies: XIST
# drives X-inactivation, so it's high in females and near-absent in males
# — exactly the same proxy-for-sex problem as the Y-chromosome genes
# above, just on the other side. It showed up as "predictive" the moment
# the Y-genes were excluded, confirming it's the same confound, not a
# real disease signal.
SEX_CONFOUND_GENES = Y_CHROMOSOME_GENES | {"XIST", "TSIX"}


def differential_expression(expr: pd.DataFrame, labels: pd.Series, lfc_threshold=1.0, padj_threshold=0.05) -> pd.DataFrame:
    """expr: genes x samples (log2-scale). Returns a genes x [log2fc, pval, padj]
    table for genes passing both thresholds, sorted by padj."""
    expr = expr.loc[~expr.index.isin(SEX_CONFOUND_GENES)]

    sle = expr.loc[:, labels[labels == "SLE"].index]
    healthy = expr.loc[:, labels[labels == "Healthy"].index]

    log2fc = sle.mean(axis=1) - healthy.mean(axis=1)
    pvals = pd.Series(
        [stats.ttest_ind(sle.loc[g], healthy.loc[g], equal_var=False).pvalue for g in expr.index],
        index=expr.index,
    )
    # genes with zero variance in both groups produce NaN p-values — not
    # differentially expressed by definition, exclude rather than crash
    valid = pvals.notna()
    log2fc, pvals = log2fc[valid], pvals[valid]

    _, padj, _, _ = multipletests(pvals.values, method="fdr_bh")
    result = pd.DataFrame({"log2fc": log2fc, "pval": pvals, "padj": padj}, index=pvals.index)
    deg = result[(result["log2fc"].abs() > lfc_threshold) & (result["padj"] < padj_threshold)]
    return deg.sort_values("padj")


def lasso_select(expr: pd.DataFrame, labels: pd.Series, deg_genes: list[str]) -> tuple[list[str], StandardScaler, LogisticRegressionCV]:
    """LASSO logistic regression on the DEG-filtered genes, 5-fold CV to
    pick C. Returns the genes with non-zero coefficients."""
    X = expr.loc[deg_genes].T  # samples x genes
    y = (labels.loc[X.index] == "SLE").astype(int)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = LogisticRegressionCV(
        Cs=10, cv=5, penalty="l1", solver="liblinear", class_weight="balanced",
        scoring="roc_auc", max_iter=5000, random_state=42,
    )
    model.fit(X_scaled, y)

    coefs = pd.Series(model.coef_[0], index=deg_genes)
    selected = coefs[coefs != 0].index.tolist()
    return selected, scaler, model


def select_features(expr: pd.DataFrame, labels: pd.Series) -> dict:
    deg = differential_expression(expr, labels)
    selected_genes, scaler, lasso_model = lasso_select(expr, labels, deg.index.tolist())
    return {
        "deg_table": deg,
        "selected_genes": selected_genes,
        "scaler": scaler,
        "best_C": lasso_model.C_[0],
    }


if __name__ == "__main__":
    from preprocess import load_and_preprocess_training

    expr, labels = load_and_preprocess_training()
    result = select_features(expr, labels)
    print(f"DEG filter: {len(result['deg_table'])} genes pass |log2FC|>1.0 and padj<0.05")
    print(f"LASSO (best C={result['best_C']:.4f}): {len(result['selected_genes'])} genes with non-zero coefficients")
    print("Selected genes:", result["selected_genes"])

    os.makedirs("../data/processed", exist_ok=True)
    with open("../data/processed/selected_genes.json", "w") as f:
        json.dump(result["selected_genes"], f, indent=2)
    print("Saved to data/processed/selected_genes.json")
