def test_explain_returns_shap_values(client, real_sle_expression):
    predict_resp = client.post("/api/predict", json={"gene_expression": real_sle_expression})
    prediction_id = predict_resp.json()["prediction_id"]

    resp = client.post("/api/explain", json={"prediction_id": prediction_id})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["shap_values"]) > 0
    for contrib in body["shap_values"]:
        assert contrib["direction"] in ("risk", "protective")


def test_explain_invalid_id_returns_404(client):
    resp = client.post("/api/explain", json={"prediction_id": "does-not-exist"})
    assert resp.status_code == 404


def test_explain_sle_sample_shows_mostly_risk_direction(client, real_sle_expression):
    """A real, known SLE sample's top SHAP contributions should mostly
    point toward 'risk' — a sanity check on the explanation direction,
    not just that the endpoint returns something."""
    predict_resp = client.post("/api/predict", json={"gene_expression": real_sle_expression})
    prediction_id = predict_resp.json()["prediction_id"]
    resp = client.post("/api/explain", json={"prediction_id": prediction_id})
    contributions = resp.json()["shap_values"]
    risk_count = sum(1 for c in contributions if c["direction"] == "risk" and c["value"] != 0)
    protective_count = sum(1 for c in contributions if c["direction"] == "protective" and c["value"] != 0)
    assert risk_count >= protective_count
