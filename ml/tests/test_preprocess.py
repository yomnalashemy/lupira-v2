"""Unit tests for preprocess.py's pure logic, using small synthetic data
— fast and network-free. The pipeline's correctness against real GEO
data was verified manually during development (real sample counts,
real label distributions, real value ranges all checked by hand); these
tests guard the transformation logic itself against regressions."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import numpy as np
import pandas as pd
import pytest

from preprocess import log2_transform_if_needed, probe_to_gene, quantile_normalize


def test_log2_transformation_applied_when_raw_scale():
    # raw-scale values (max > 100) should get log2(x+1)
    df = pd.DataFrame({"s1": [10.0, 500.0], "s2": [20.0, 1000.0]}, index=["gene_a", "gene_b"])
    result = log2_transform_if_needed(df)
    assert result.loc["gene_b", "s2"] == pytest.approx(np.log2(1001.0))
    assert result.max().max() < 15


def test_log2_transformation_skipped_when_already_log_scale():
    # already log2-scale values (max <= 100, realistically <20) should
    # pass through unchanged
    df = pd.DataFrame({"s1": [2.0, 8.0], "s2": [3.0, 10.0]}, index=["gene_a", "gene_b"])
    result = log2_transform_if_needed(df)
    pd.testing.assert_frame_equal(result, df)


def test_probe_to_gene_reduces_duplicate_probes_per_gene():
    # two probes map to the same gene — the higher-variance one should
    # be kept, the lower-variance one dropped
    expr = pd.DataFrame(
        {"s1": [1.0, 1.0, 5.0], "s2": [1.1, 9.0, 5.1], "s3": [0.9, 2.0, 4.9]},
        index=["probe_low_var", "probe_high_var", "probe_unique"],
    )
    gpl = pd.DataFrame({
        "ID": ["probe_low_var", "probe_high_var", "probe_unique"],
        "Gene Symbol": ["GENE_A", "GENE_A", "GENE_B"],
    })
    result = probe_to_gene(expr, gpl)
    assert list(result.index) == ["GENE_A", "GENE_B"]
    # the kept GENE_A row should be the high-variance probe's values
    assert result.loc["GENE_A", "s2"] == 9.0


def test_probe_to_gene_drops_unmapped_probes():
    expr = pd.DataFrame({"s1": [1.0, 2.0]}, index=["mapped_probe", "unmapped_probe"])
    gpl = pd.DataFrame({"ID": ["mapped_probe"], "Gene Symbol": ["GENE_A"]})
    result = probe_to_gene(expr, gpl)
    assert list(result.index) == ["GENE_A"]


def test_probe_to_gene_drops_blank_gene_symbols():
    expr = pd.DataFrame({"s1": [1.0, 2.0]}, index=["p1", "p2"])
    gpl = pd.DataFrame({"ID": ["p1", "p2"], "Gene Symbol": ["GENE_A", ""]})
    result = probe_to_gene(expr, gpl)
    assert list(result.index) == ["GENE_A"]


def test_quantile_normalization_equalizes_distributions():
    # three samples with different distributions but the same rank
    # order per gene should end up with identical sorted values after
    # quantile normalization
    df = pd.DataFrame({
        "s1": [1.0, 2.0, 3.0],
        "s2": [10.0, 20.0, 30.0],
        "s3": [100.0, 150.0, 400.0],
    })
    result = quantile_normalize(df)
    for col in result.columns:
        assert np.allclose(sorted(result[col]), sorted(result["s1"]))
