def test_predict_valid_input_returns_200(client, real_sle_expression):
    resp = client.post("/api/predict", json={"gene_expression": real_sle_expression})
    assert resp.status_code == 200
    body = resp.json()
    assert body["prediction"] in ("SLE", "Healthy")
    assert 0.0 <= body["probability"]["SLE"] <= 1.0
    assert abs(body["probability"]["SLE"] + body["probability"]["Healthy"] - 1.0) < 1e-6


def test_predict_correctly_classifies_real_sle_sample(client, real_sle_expression):
    resp = client.post("/api/predict", json={"gene_expression": real_sle_expression})
    assert resp.json()["prediction"] == "SLE"


def test_predict_correctly_classifies_real_healthy_sample(client, real_healthy_expression):
    resp = client.post("/api/predict", json={"gene_expression": real_healthy_expression})
    assert resp.json()["prediction"] == "Healthy"


def test_predict_missing_genes_still_returns_200_with_partial_count(client, real_sle_expression):
    partial = dict(list(real_sle_expression.items())[:5])
    resp = client.post("/api/predict", json={"gene_expression": partial})
    assert resp.status_code == 200
    assert resp.json()["genes_used"] == 5


def test_predict_empty_expression_returns_200_all_genes_missing(client):
    resp = client.post("/api/predict", json={"gene_expression": {}})
    assert resp.status_code == 200
    assert resp.json()["genes_used"] == 0


def test_predict_malformed_request_returns_422(client):
    resp = client.post("/api/predict", json={"gene_expression": "not a dict"})
    assert resp.status_code == 422


def test_predict_stores_in_database(client, real_sle_expression):
    """Storage is now bookkeeping only — /explain no longer depends on
    it (see test_explain.py) — so check the row directly rather than
    through another endpoint."""
    from app.models.db import Prediction, SessionLocal

    resp = client.post("/api/predict", json={"gene_expression": real_sle_expression, "patient_id": "p-123"})
    prediction_id = resp.json()["prediction_id"]

    db = SessionLocal()
    try:
        row = db.get(Prediction, prediction_id)
        assert row is not None
        assert row.patient_id == "p-123"
    finally:
        db.close()


def test_predict_typical_input_flagged_typical(client, real_sle_expression):
    resp = client.post("/api/predict", json={"gene_expression": real_sle_expression})
    body = resp.json()
    assert body["input_quality"] == "typical"
    assert body["input_quality_note"] is None


def test_predict_wildly_different_scale_flagged_unusual(client, real_sle_expression):
    """A real sample's values scaled 1000x land nowhere near the training
    distribution (log2 intensities, roughly 2-16) — simulating e.g. raw
    RNA-seq counts or a different platform's units uploaded by mistake.
    This should be flagged, not silently scored as if it were valid."""
    shifted = {gene: value * 1000 for gene, value in real_sle_expression.items()}
    resp = client.post("/api/predict", json={"gene_expression": shifted})
    body = resp.json()
    assert body["input_quality"] == "unusual"
    assert body["input_quality_note"] is not None


def test_predict_missing_genes_imputed_as_training_mean_not_zero(client, real_sle_expression):
    """Regression check for the imputation bug: a missing gene used to be
    filled with raw 0, which becomes a large-magnitude z-score once run
    through the training scaler (log2 intensities are never near 0) —
    silently telling the model "very low expression" instead of "unknown".
    Dropping most genes should still be flagged typical as long as the
    few genes that ARE present are on-scale, since the rest are now
    imputed at the training mean (z=0), not an extreme value."""
    partial = dict(list(real_sle_expression.items())[:5])
    resp = client.post("/api/predict", json={"gene_expression": partial})
    body = resp.json()
    assert body["genes_used"] == 5
    assert body["input_quality"] == "typical"


def test_confidence_thresholds_correct(client, real_sle_expression, real_healthy_expression):
    for expr in (real_sle_expression, real_healthy_expression):
        resp = client.post("/api/predict", json={"gene_expression": expr})
        body = resp.json()
        top_p = max(body["probability"]["SLE"], body["probability"]["Healthy"])
        if body["confidence"] == "high":
            assert top_p > 0.85
        elif body["confidence"] == "moderate":
            assert 0.65 < top_p <= 0.85
        else:
            assert top_p <= 0.65
