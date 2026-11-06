def test_explain_returns_shap_values(client, real_sle_expression):
    resp = client.post("/api/explain", json={"gene_expression": real_sle_expression})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["shap_values"]) > 0
    for contrib in body["shap_values"]:
        assert contrib["direction"] in ("risk", "protective")


def test_explain_empty_expression_returns_200_all_genes_missing(client):
    """/explain takes gene expression directly (not a prediction_id to
    look up), so the edge case to guard is missing genes, same as
    /predict's — not a not-found id, since there's no longer an id."""
    resp = client.post("/api/explain", json={"gene_expression": {}})
    assert resp.status_code == 200


def test_explain_sle_sample_shows_mostly_risk_direction(client, real_sle_expression):
    """A real, known SLE sample's top SHAP contributions should mostly
    point toward 'risk' — a sanity check on the explanation direction,
    not just that the endpoint returns something."""
    resp = client.post("/api/explain", json={"gene_expression": real_sle_expression})
    contributions = resp.json()["shap_values"]
    risk_count = sum(1 for c in contributions if c["direction"] == "risk" and c["value"] != 0)
    protective_count = sum(1 for c in contributions if c["direction"] == "protective" and c["value"] != 0)
    assert risk_count >= protective_count
