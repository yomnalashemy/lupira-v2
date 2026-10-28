"""NPSLE (neuropsychiatric lupus) risk scoring — rule-based, not ML.

Important distinction, worth keeping straight: the 19-syndrome LIST
below is the real ACR 1999 case definitions for NPSLE, a genuine
published clinical standard. The SEVERITY WEIGHTS and risk-category
thresholds are NOT part of that standard — the original ACR paper
classifies which syndromes count as NPSLE, it does not assign them a
severity score. The weights here are a clinically-reasonable default
(life-threatening/major CNS events weighted higher than common,
less-specific symptoms), constructed for this tool, not copied from a
specific validated scoring instrument. Flag this plainly rather than
let "rule-based, implements a published standard" imply the scoring
itself is independently validated — it isn't, yet. A rheumatologist
or neurologist should review the weights before any real clinical use.
"""
from __future__ import annotations

NPSLE_SYNDROMES = {
    "central": [
        "Aseptic meningitis",
        "Cerebrovascular disease",
        "Demyelinating syndrome",
        "Headache (intractable)",
        "Movement disorder (chorea)",
        "Myelopathy",
        "Seizure disorders",
        "Acute confusional state",
        "Anxiety disorder",
        "Cognitive dysfunction",
        "Mood disorder",
        "Psychosis",
    ],
    "peripheral": [
        "Acute inflammatory demyelinating polyradiculoneuropathy (Guillain-Barré)",
        "Autonomic disorder",
        "Mononeuropathy (single/multiplex)",
        "Myasthenia gravis",
        "Cranial neuropathy",
        "Plexopathy",
        "Polyneuropathy",
    ],
}

ALL_SYNDROMES = {s: cat for cat, syndromes in NPSLE_SYNDROMES.items() for s in syndromes}

# 1-10 scale: life-threatening / major irreversible-deficit syndromes at
# the top, common but nonspecific/self-limiting symptoms at the bottom.
# See module docstring — this is a constructed default, not a cited score.
SEVERITY_WEIGHTS = {
    "Seizure disorders": 10,
    "Psychosis": 10,
    "Cerebrovascular disease": 10,
    "Myelopathy": 10,
    "Acute inflammatory demyelinating polyradiculoneuropathy (Guillain-Barré)": 9,
    "Acute confusional state": 8,
    "Demyelinating syndrome": 8,
    "Aseptic meningitis": 7,
    "Myasthenia gravis": 7,
    "Movement disorder (chorea)": 6,
    "Cognitive dysfunction": 6,
    "Mononeuropathy (single/multiplex)": 5,
    "Plexopathy": 5,
    "Polyneuropathy": 5,
    "Autonomic disorder": 4,
    "Cranial neuropathy": 4,
    "Mood disorder": 3,
    "Headache (intractable)": 2,
    "Anxiety disorder": 2,
}

RISK_CATEGORIES = [(0, "Low"), (10, "Moderate"), (25, "High"), (40, "Critical")]

CONFOUNDING_DISCOUNT = {
    "none": 1.0,
    "medication_side_effect": 0.5,
    "infection": 0.4,
    "metabolic_disturbance": 0.5,
    "pre_existing_condition": 0.3,
}

TEMPORAL_WEIGHT = {
    "within_3_months": 1.0,
    "within_12_months": 0.85,
    "over_12_months": 0.6,
    "unknown": 0.7,
}


def categorize_score(score: float) -> str:
    category = RISK_CATEGORIES[0][1]
    for threshold, name in RISK_CATEGORIES:
        if score >= threshold:
            category = name
    return category


def attribution_label(confidence: float) -> str:
    if confidence >= 0.8:
        return "definitely_sle"
    if confidence >= 0.4:
        return "possibly_sle"
    return "likely_non_sle"


def score_npsle(
    syndromes: list[str],
    sle_diagnosis_confirmed: bool,
    temporal_relation: str = "unknown",
    confounding_factors: list[str] | None = None,
) -> dict:
    confounding_factors = confounding_factors or []
    unknown = [s for s in syndromes if s not in ALL_SYNDROMES]
    if unknown:
        raise ValueError(f"Unrecognized syndrome(s) not in the ACR 1999 list: {unknown}")

    temporal_factor = TEMPORAL_WEIGHT.get(temporal_relation, TEMPORAL_WEIGHT["unknown"])
    confound_factor = min((CONFOUNDING_DISCOUNT.get(f, 0.7) for f in confounding_factors), default=1.0)
    sle_factor = 1.0 if sle_diagnosis_confirmed else 0.5

    matched = []
    total_score = 0.0
    for s in syndromes:
        weight = SEVERITY_WEIGHTS.get(s, 3)
        confidence = temporal_factor * confound_factor * sle_factor
        contribution = weight * confidence
        total_score += contribution
        matched.append({
            "name": s,
            "category": ALL_SYNDROMES[s],
            "weight": weight,
            "attribution": attribution_label(confidence),
        })

    return {
        "risk_score": round(total_score, 1),
        "risk_category": categorize_score(total_score),
        "matched_syndromes": matched,
        "note": (
            "This is a screening tool based on ACR 1999 case definitions for "
            "NPSLE syndrome classification. The severity weighting is a "
            "constructed default, not an independently validated clinical "
            "score. Clinical assessment by a rheumatologist and neurologist "
            "is required for diagnosis."
        ),
    }


if __name__ == "__main__":
    print("All 19 syndromes:", len(ALL_SYNDROMES))

    print("\n--- No syndromes ---")
    r = score_npsle([], sle_diagnosis_confirmed=True)
    print(r["risk_score"], r["risk_category"])
    assert r["risk_score"] == 0.0 and r["risk_category"] == "Low"

    print("\n--- All syndromes, confirmed SLE, recent, no confounders ---")
    r = score_npsle(list(ALL_SYNDROMES), sle_diagnosis_confirmed=True, temporal_relation="within_3_months")
    print(r["risk_score"], r["risk_category"])
    assert r["risk_category"] == "Critical"

    print("\n--- Example from the spec: cognitive dysfunction, headache, mood disorder ---")
    r = score_npsle(
        ["Cognitive dysfunction", "Headache (intractable)", "Mood disorder"],
        sle_diagnosis_confirmed=True,
        temporal_relation="within_12_months",
        confounding_factors=["medication_side_effect"],
    )
    import json

    print(json.dumps(r, indent=2))

    print("\n--- Same syndromes, but with a confounding factor vs without ---")
    r_no_confound = score_npsle(["Cognitive dysfunction"], sle_diagnosis_confirmed=True, temporal_relation="within_3_months")
    r_confound = score_npsle(
        ["Cognitive dysfunction"], sle_diagnosis_confirmed=True, temporal_relation="within_3_months",
        confounding_factors=["infection"],
    )
    print(f"no confound: {r_no_confound['risk_score']}, with confound: {r_confound['risk_score']}")
    assert r_confound["risk_score"] < r_no_confound["risk_score"], "confounding factors should lower the score"

    print("\nAll checks passed.")
