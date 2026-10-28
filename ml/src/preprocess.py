"""Loading and preprocessing for the SLE gene-expression datasets.

Training: GSE50772 only (Affymetrix HG-U133 Plus 2.0, 81 samples).
External validation: GSE72509 (Illumina RNA-seq RPKM) and GSE49454
(Illumina HumanHT-12), kept separate from training and from each
other — never merged with GSE50772. See the project notes on why:
GSE72509 is a different measurement technology (RNA-seq, not
microarray), so ComBat-merging it with GSE50772 would combine values
that are not on a comparable scale.
"""
from __future__ import annotations

import logging
import re

import GEOparse
import numpy as np
import pandas as pd

logging.getLogger("GEOparse").setLevel(logging.ERROR)

RAW_DIR = "./data/raw"


def load_gse(geo_id: str):
    return GEOparse.get_GEO(geo=geo_id, destdir=RAW_DIR)


def build_expression_matrix(gse) -> pd.DataFrame:
    """Probes (rows) x samples (cols), raw VALUE from each GSM's table."""
    series = {}
    for gsm_id, gsm in gse.gsms.items():
        if gsm.table.empty or "VALUE" not in gsm.table.columns:
            continue
        series[gsm_id] = gsm.table.set_index("ID_REF")["VALUE"]
    if not series:
        raise ValueError(
            f"No per-sample VALUE tables found for this series — "
            f"it may publish data via a supplementary file instead."
        )
    return pd.DataFrame(series)


def extract_labels_disease_status(gse) -> pd.Series:
    """For series using 'disease status: X' in characteristics_ch1."""
    labels = {}
    for gsm_id, gsm in gse.gsms.items():
        chars = gsm.metadata.get("characteristics_ch1", [])
        status = next((c for c in chars if c.lower().startswith("disease status:")), None)
        if status is None:
            continue
        value = status.split(":", 1)[1].strip().lower()
        labels[gsm_id] = "SLE" if "sle" in value or "lupus" in value else "Healthy"
    return pd.Series(labels, name="label")


def extract_labels_group_field(gse) -> pd.Series:
    """For series using 'group: X' in characteristics_ch1 (e.g. GSE49454)."""
    labels = {}
    for gsm_id, gsm in gse.gsms.items():
        chars = gsm.metadata.get("characteristics_ch1", [])
        group = next((c for c in chars if c.lower().startswith("group:")), None)
        if group is None:
            continue
        value = group.split(":", 1)[1].strip().lower()
        labels[gsm_id] = "SLE" if "sle" in value else "Healthy"
    return pd.Series(labels, name="label")


def log2_transform_if_needed(df: pd.DataFrame) -> pd.DataFrame:
    """Per the spec: if values look raw-scale (max > 100), apply log2(x+1)."""
    if df.max().max() > 100:
        return np.log2(df.clip(lower=0) + 1)
    return df


def probe_to_gene(expr: pd.DataFrame, gpl_table: pd.DataFrame) -> pd.DataFrame:
    """Collapse probes to gene symbols, keeping the highest-variance probe
    per gene when multiple probes map to the same symbol."""
    mapping = gpl_table.set_index("ID")["Gene Symbol"].dropna()
    mapping = mapping[mapping.str.strip() != ""]
    expr = expr.loc[expr.index.intersection(mapping.index)].copy()
    expr["__gene__"] = mapping.loc[expr.index]
    expr["__variance__"] = expr.drop(columns="__gene__").var(axis=1)
    expr = expr.sort_values("__variance__", ascending=False)
    expr = expr.drop_duplicates(subset="__gene__", keep="first")
    expr = expr.set_index("__gene__").drop(columns="__variance__")
    expr.index.name = "gene"
    return expr


def quantile_normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Standard quantile normalization across samples (columns)."""
    ranked = df.rank(method="average")
    sorted_means = df.apply(np.sort, axis=0).mean(axis=1).values
    quantile_df = pd.DataFrame(
        {col: np.interp(ranked[col], np.arange(1, len(df) + 1), sorted_means) for col in df.columns},
        index=df.index,
    )
    return quantile_df


def load_and_preprocess_training() -> tuple[pd.DataFrame, pd.Series]:
    """GSE50772: expression (genes x samples, log2 + quantile-normalized,
    gene-symbol indexed) and labels."""
    gse = load_gse("GSE50772")
    expr = build_expression_matrix(gse)
    labels = extract_labels_disease_status(gse)
    common = expr.columns.intersection(labels.index)
    expr, labels = expr[common], labels[common]

    expr = log2_transform_if_needed(expr)
    gpl = list(gse.gpls.values())[0]
    expr = probe_to_gene(expr, gpl.table)
    expr = quantile_normalize(expr)
    return expr, labels


if __name__ == "__main__":
    expr, labels = load_and_preprocess_training()
    print("Expression matrix shape (genes x samples):", expr.shape)
    print("Label counts:\n", labels.value_counts())
    print("Value range after log2 + quantile norm:", expr.values.min(), "to", expr.values.max())
    print("Any NaNs:", expr.isna().any().any())
    print(expr.iloc[:5, :5])
