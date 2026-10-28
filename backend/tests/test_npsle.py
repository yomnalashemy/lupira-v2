def test_npsle_score_valid_input(client):
    resp = client.post(
        "/api/npsle-score",
        json={
            "syndromes": ["Cognitive dysfunction", "Headache (intractable)", "Mood disorder"],
            "sle_diagnosis_confirmed": True,
            "temporal_relation": "within_12_months",
            "confounding_factors": ["medication_side_effect"],
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["risk_category"] in ("Low", "Moderate", "High", "Critical")
    assert len(body["matched_syndromes"]) == 3


def test_npsle_empty_syndromes(client):
    resp = client.post("/api/npsle-score", json={"syndromes": [], "sle_diagnosis_confirmed": True})
    assert resp.status_code == 200
    body = resp.json()
    assert body["risk_score"] == 0.0
    assert body["risk_category"] == "Low"


def test_npsle_unrecognized_syndrome_returns_422(client):
    resp = client.post("/api/npsle-score", json={"syndromes": ["Not a real syndrome"], "sle_diagnosis_confirmed": True})
    assert resp.status_code == 422


def test_npsle_attribution_rules(client):
    resp = client.post(
        "/api/npsle-score",
        json={
            "syndromes": ["Seizure disorders"],
            "sle_diagnosis_confirmed": True,
            "temporal_relation": "within_3_months",
            "confounding_factors": ["infection"],
        },
    )
    body = resp.json()
    assert body["matched_syndromes"][0]["attribution"] in ("possibly_sle", "likely_non_sle")
