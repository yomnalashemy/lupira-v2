"""Unit tests for models.py, using small synthetic classification data
— fast and network-free."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import numpy as np
import pytest
from sklearn.datasets import make_classification

from models import build_grids, train_all


@pytest.fixture(scope="module")
def synthetic_data():
    X, y = make_classification(
        n_samples=60, n_features=10, n_informative=6, n_redundant=2,
        weights=[0.75, 0.25], random_state=42,
    )
    return X, y


@pytest.fixture(scope="module")
def trained_models(synthetic_data):
    X, y = synthetic_data
    # tiny grids so this runs in under a second, not the full spec grid
    import models as models_module

    original_build_grids = models_module.build_grids

    def tiny_grids(scale_pos_weight):
        full = original_build_grids(scale_pos_weight)
        return {
            "SVM": (full["SVM"][0], {"C": [1], "gamma": ["scale"]}),
            "RandomForest": (full["RandomForest"][0], {"n_estimators": [50], "max_depth": [5], "min_samples_leaf": [1]}),
            "XGBoost": (full["XGBoost"][0], {"n_estimators": [50], "max_depth": [3], "learning_rate": [0.1]}),
            "MLP": (full["MLP"][0], {"hidden_layer_sizes": [(16,)], "alpha": [0.001]}),
        }

    models_module.build_grids = tiny_grids
    try:
        return train_all(X, y)
    finally:
        models_module.build_grids = original_build_grids


def test_build_grids_returns_all_four_models():
    grids = build_grids(scale_pos_weight=1.0)
    assert set(grids.keys()) == {"SVM", "RandomForest", "XGBoost", "MLP"}


def test_class_weight_balancing_applied():
    grids = build_grids(scale_pos_weight=2.5)
    svm_estimator, _ = grids["SVM"]
    assert svm_estimator.class_weight == "balanced"
    rf_estimator, _ = grids["RandomForest"]
    assert rf_estimator.class_weight == "balanced"
    xgb_estimator, _ = grids["XGBoost"]
    assert xgb_estimator.scale_pos_weight == 2.5


def test_all_four_models_train_without_error(trained_models):
    assert set(trained_models.keys()) == {"SVM", "RandomForest", "XGBoost", "MLP"}
    for name, search in trained_models.items():
        assert hasattr(search, "best_estimator_"), f"{name} did not produce a fitted estimator"


def test_all_models_return_valid_probabilities(trained_models, synthetic_data):
    X, _ = synthetic_data
    for name, search in trained_models.items():
        proba = search.predict_proba(X[:5])
        assert proba.shape == (5, 2)
        assert np.allclose(proba.sum(axis=1), 1.0)
        assert (proba >= 0).all() and (proba <= 1).all()


def test_model_serialization_roundtrip(trained_models, synthetic_data, tmp_path):
    import joblib

    X, _ = synthetic_data
    model = trained_models["RandomForest"].best_estimator_
    path = tmp_path / "model.joblib"
    joblib.dump(model, path)
    loaded = joblib.load(path)
    np.testing.assert_array_equal(model.predict(X[:5]), loaded.predict(X[:5]))
