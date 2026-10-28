import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest

from npsle import ALL_SYNDROMES, NPSLE_SYNDROMES, score_npsle


def test_all_19_syndromes_recognized():
    assert len(ALL_SYNDROMES) == 19
    assert len(NPSLE_SYNDROMES["central"]) == 12
    assert len(NPSLE_SYNDROMES["peripheral"]) == 7


def test_scoring_with_no_syndromes_returns_zero():
    result = score_npsle([], sle_diagnosis_confirmed=True)
    assert result["risk_score"] == 0.0
    assert result["risk_category"] == "Low"


def test_scoring_with_all_syndromes_returns_critical():
    result = score_npsle(
        list(ALL_SYNDROMES), sle_diagnosis_confirmed=True, temporal_relation="within_3_months"
    )
    assert result["risk_category"] == "Critical"


def test_attribution_respects_confounding_factors():
    no_confound = score_npsle(
        ["Cognitive dysfunction"], sle_diagnosis_confirmed=True, temporal_relation="within_3_months"
    )
    with_confound = score_npsle(
        ["Cognitive dysfunction"], sle_diagnosis_confirmed=True, temporal_relation="within_3_months",
        confounding_factors=["infection"],
    )
    assert with_confound["risk_score"] < no_confound["risk_score"]
    assert with_confound["matched_syndromes"][0]["attribution"] != "definitely_sle"


def test_unrecognized_syndrome_raises():
    with pytest.raises(ValueError):
        score_npsle(["Not a real syndrome"], sle_diagnosis_confirmed=True)


def test_unconfirmed_sle_diagnosis_lowers_score():
    confirmed = score_npsle(["Seizure disorders"], sle_diagnosis_confirmed=True, temporal_relation="within_3_months")
    unconfirmed = score_npsle(["Seizure disorders"], sle_diagnosis_confirmed=False, temporal_relation="within_3_months")
    assert unconfirmed["risk_score"] < confirmed["risk_score"]


def test_matched_syndromes_report_correct_category():
    result = score_npsle(["Seizure disorders", "Polyneuropathy"], sle_diagnosis_confirmed=True)
    categories = {m["name"]: m["category"] for m in result["matched_syndromes"]}
    assert categories["Seizure disorders"] == "central"
    assert categories["Polyneuropathy"] == "peripheral"
