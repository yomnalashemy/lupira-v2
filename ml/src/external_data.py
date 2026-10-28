"""Loading + preprocessing for the two external validation sets. Each is
self-normalized independently (z-scored within itself) rather than
jointly normalized with training data — that's deliberate: GSE50772
(training) is Affymetrix, GSE49454 is Illumina, GSE72509 is RNA-seq, so
absolute scale is never comparable across them. Self-normalization tests
whether the RELATIVE expression pattern of the selected genes
generalizes, which is the real question for cross-platform validation.
"""
from __future__ import annotations

import gzip
import io
import logging

import GEOparse
import numpy as np
import pandas as pd
import requests

logging.getLogger("GEOparse").setLevel(logging.ERROR)

RAW_DIR = "../data/raw"


def load_gse49454() -> tuple[pd.DataFrame, pd.Series]:
    """Illumina HumanHT-12 (GPL10558). Returns (genes x samples z-scored, labels)."""
    gse = GEOparse.get_GEO(geo="GSE49454", destdir=RAW_DIR)

    series = {}
    for gsm_id, gsm in gse.gsms.items():
        if gsm.table.empty or "VALUE" not in gsm.table.columns:
            continue
        series[gsm_id] = gsm.table.set_index("ID_REF")["VALUE"]
    expr = pd.DataFrame(series)

    labels = {}
    for gsm_id, gsm in gse.gsms.items():
        chars = gsm.metadata.get("characteristics_ch1", [])
        group = next((c for c in chars if c.lower().startswith("group:")), None)
        if group is None:
            continue
        labels[gsm_id] = "SLE" if "sle" in group.lower() and "healthy" not in group.lower() else "Healthy"
    labels = pd.Series(labels, name="label")

    common = expr.columns.intersection(labels.index)
    expr, labels = expr[common], labels[common]

    if expr.max().max() > 100:
        expr = np.log2(expr.clip(lower=0) + 1)

    gpl = list(gse.gpls.values())[0]
    mapping = gpl.table.set_index("ID")["Symbol"].dropna()
    mapping = mapping[mapping.astype(str).str.strip() != ""]
    expr = expr.loc[expr.index.intersection(mapping.index)].copy()
    expr["__gene__"] = mapping.loc[expr.index]
    expr["__variance__"] = expr.drop(columns="__gene__").var(axis=1)
    expr = expr.sort_values("__variance__", ascending=False).drop_duplicates(subset="__gene__", keep="first")
    expr = expr.set_index("__gene__").drop(columns="__variance__")
    expr.index.name = "gene"

    expr = expr.sub(expr.mean(axis=1), axis=0).div(expr.std(axis=1).replace(0, 1), axis=0)
    return expr, labels


def load_gse72509() -> tuple[pd.DataFrame, pd.Series]:
    """RNA-seq RPKM via the series supplementary file (no per-GSM tables
    for this series — see the platform-mismatch finding). The file's own
    sample columns are named by title (SLE52, control3, ...), which is
    simpler and less error-prone than round-tripping through GSM ids.
    Returns (genes x samples z-scored, labels)."""
    url = "https://ftp.ncbi.nlm.nih.gov/geo/series/GSE72nnn/GSE72509/suppl/GSE72509_SLE_RPKMs.txt.gz"
    resp = requests.get(url, timeout=120)
    resp.raise_for_status()
    with gzip.open(io.BytesIO(resp.content)) as f:
        raw = pd.read_csv(f, sep="\t", index_col=0)

    meta_cols = {"CHR", "START", "END", "STR", "COORDS", "SIZE", "TYPE", "SYMBOL", "DESC", "FEATURE_ID"}
    sample_cols = [c for c in raw.columns if c not in meta_cols]
    expr = raw[sample_cols].copy()
    expr["__gene__"] = raw["SYMBOL"]

    labels = pd.Series(
        {c: ("SLE" if c.lower().startswith("sle") else "Healthy") for c in sample_cols}, name="label"
    )

    if expr.drop(columns="__gene__").max().max() > 100:
        expr[sample_cols] = np.log2(expr[sample_cols].clip(lower=0) + 1)

    expr = expr.dropna(subset=["__gene__"])
    expr = expr[expr["__gene__"].astype(str).str.strip() != ""]
    expr["__variance__"] = expr[sample_cols].var(axis=1)
    expr = expr.sort_values("__variance__", ascending=False).drop_duplicates(subset="__gene__", keep="first")
    expr = expr.set_index("__gene__")[sample_cols]
    expr.index.name = "gene"

    expr = expr.sub(expr.mean(axis=1), axis=0).div(expr.std(axis=1).replace(0, 1), axis=0)
    return expr, labels


if __name__ == "__main__":
    print("=== GSE49454 ===")
    expr49454, labels49454 = load_gse49454()
    print("shape:", expr49454.shape, "labels:", labels49454.value_counts().to_dict())

    print("\n=== GSE72509 ===")
    expr72509, labels72509 = load_gse72509()
    print("shape:", expr72509.shape, "labels:", labels72509.value_counts().to_dict())
