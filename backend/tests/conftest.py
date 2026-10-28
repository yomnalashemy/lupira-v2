import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient

from app.main import app

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def real_sle_expression():
    """A real GSE50772 SLE sample's expression values for the model's
    selected genes (extracted once via the ML pipeline, saved as a
    fixture) — not synthetic data, and no GEOparse/network dependency
    in the backend's own test environment."""
    with open(FIXTURES / "real_sle_sample.json") as f:
        return json.load(f)["gene_expression"]


@pytest.fixture
def real_healthy_expression():
    with open(FIXTURES / "real_healthy_sample.json") as f:
        return json.load(f)["gene_expression"]
