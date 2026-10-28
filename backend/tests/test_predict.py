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
    resp = client.post("/api/predict", json={"gene_expression": real_sle_expression, "patient_id": "p-123"})
    prediction_id = resp.json()["prediction_id"]
    # confirmed indirectly: /explain looks it up by id, 404 means it wasn't stored
    explain_resp = client.post("/api/explain", json={"prediction_id": prediction_id})
    assert explain_resp.status_code == 200


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
