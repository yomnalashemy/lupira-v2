# Lupira — AI-Powered Lupus Diagnostic Platform

> Research tool for SLE classification using blood gene-expression profiles,
> plus NPSLE risk assessment based on ACR 1999 case definitions.

## Overview

Lupira classifies blood gene-expression samples as SLE-positive or healthy,
explains which genes drove each prediction (SHAP), and includes a separate
rule-based NPSLE (neuropsychiatric lupus) risk-screening module. The
original version was published as "AI-Lupira: A Machine Learning-Powered
Mobile System for Lupus Detection and Symptom Analysis" (MUST, 2025). This
is a full rebuild with research-grade methodology and production
engineering.

**This is a research tool, not a medical device. It is not intended for
clinical decision-making.**

## Methodology

- **Training data:** GSE50772 only (Affymetrix HG-U133 Plus 2.0, 81
  samples — 61 SLE, 20 healthy).
- **External validation:** GSE72509 (RNA-seq) and GSE49454 (Illumina), both
  fully independent of training and feature selection.
- **A deliberate deviation from the original plan worth knowing about:**
  GSE72509 was originally going to be merged into training via ComBat batch
  correction, on the assumption it was on the same platform as GSE50772.
  It isn't — GSE72509 is RNA-seq, GSE50772 is microarray. ComBat corrects
  batch effects *within* one measurement technology, not differences
  *between* technologies, so merging them would have produced numbers that
  looked combined without being scientifically comparable. GSE72509 is used
  only as a second independent external validation set instead.
- **Preprocessing:** log2 transform where needed, quantile normalization,
  probe-to-gene mapping via each platform's own annotation. Known
  sex-chromosome genes (Y-chromosome genes, XIST) are excluded from the
  candidate feature pool — SLE is genuinely female-predominant, which means
  those genes predict disease status by proxy for patient sex, not lupus
  biology, if not excluded. (Caught by inspecting an early unfiltered
  LASSO run, which had picked up `RPS4Y1`, `USP9Y`, `EIF1AY`, and `XIST`.)
- **Feature selection:** differential expression filtering (|log2FC| > 1.0,
  Benjamini-Hochberg adjusted p < 0.05), then LASSO, then **stability
  selection** across 5 resampled folds — a gene is only kept in the final
  set if selected in most folds, not just once on the full dataset. This
  exists because external validation initially showed near-chance AUC for
  3 of 4 models; checking gene-by-gene direction consistency between
  training and the external cohorts showed only ~65-73% of genes kept the
  same up/down direction, meaning some were cohort-specific noise, not
  real signal.
- **Models compared:** SVM, Random Forest, XGBoost, MLP — all four trained
  and reported, not just the best.
- **Interpretability:** SHAP (`KernelExplainer`) on the shipped model.
- **NPSLE module:** rule-based, not ML. The 19-syndrome list is the real
  ACR 1999 case definitions. The severity weights and risk-category
  thresholds are **not** part of that standard — they're a clinically
  reasonable default constructed for this tool, not an independently
  validated score. A rheumatologist or neurologist should review them
  before any real use. Flagged in the module itself and in every API
  response.

## Results

The shipped model is **SVM** — the most consistent performer across both
independent external validation sets, not just the best internal
cross-validation score.

| | Internal CV (nested, honest) | GSE72509 (RNA-seq) | GSE49454 (Illumina) |
|---|---|---|---|
| AUC | 1.000* | 0.843 | 0.768 |

\* *Internal CV AUC of exactly 1.000 is a real, checked result, not a
leakage artifact — see "Two real bugs" below for why that's a meaningful
distinction here.* Per-fold inspection shows the model's probability
*ranking* is perfect in every fold, but threshold-based classification
accuracy is not (specificity drops to 0.75 in 3 of 5 folds) — a coherent
pattern for a small dataset with a strong biological signal, not a
degenerate classifier.

Full metrics: `ml/results/comparison_table.csv`,
`ml/results/external_validation.csv`. SHAP plots:
`ml/results/shap_summary_beeswarm.png`, `ml/results/shap_bar.png`.

### Two real bugs found during development (worth knowing about)

1. **Feature-selection leakage.** The first evaluation ran DEG+LASSO once
   on all 81 training samples, then cross-validated on those same
   samples — every fold's "held-out" data had already influenced which
   genes were selected. This produced impossible-looking perfect AUC
   (1.000) for 3 of 4 models. Fixed by redoing feature selection
   independently inside each CV fold (`ml/src/evaluate.py:nested_cv_evaluate`).
2. **A scaling double-transform.** External validation data is
   self-z-scored per gene within its own cohort (since its raw scale isn't
   comparable to training's). An early version then ran that *already
   z-scored* data through the *training-fitted* `StandardScaler` a second
   time — subtracting training's raw log2-intensity mean (~8-10) from
   values that were already ~0. This produced a near-constant large
   offset for every sample regardless of label, and explained external
   AUC collapsing to ~0.5 (random chance) for every model. Fixed in
   `ml/src/external_validate.py:score_external` — self-standardized
   external data goes to the models directly, not through the training
   scaler again. External AUC went from ~0.50 to 0.60–0.84 once fixed.

## Quick Start

### Docker (recommended)

```bash
docker compose up --build
```

- Backend: http://localhost:8000 (docs at `/docs`)
- Frontend: http://localhost:3000

### Manual setup

**ML pipeline** (optional — re-runs feature selection/training/evaluation
from scratch against the real GEO datasets; the backend already ships with
pre-exported artifacts, so this isn't required to run the app):

```bash
cd ml
python -m venv .venv && .venv/bin/pip install -r requirements.txt
python src/export.py   # downloads real data, trains, evaluates, exports to backend/app/artifacts/
python -m pytest tests/ -v
```

**Backend:**

```bash
cd backend
python -m venv .venv && .venv/bin/pip install -r requirements.txt
uvicorn app.main:app --reload
python -m pytest tests/ -v
```

**Frontend:**

```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000/api npm run dev
```

## Architecture

```
lupira/
├── ml/          # data pipeline, feature selection, model training, evaluation, SHAP, NPSLE logic
├── backend/     # FastAPI service — /predict, /explain, /npsle-score, /health, /model-info
├── frontend/    # Next.js app — upload, predict, SHAP visualization, NPSLE form, methodology page
└── docker-compose.yml
```

## API

See `backend/app/routes/` for the live route definitions, or run the
backend and visit `/docs` for interactive Swagger UI.

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/predict` | POST | Gene expression → SLE/Healthy classification |
| `/api/explain` | POST | SHAP gene-level explanation for a prior prediction |
| `/api/npsle-score` | POST | ACR 1999-based NPSLE syndrome risk screening |
| `/api/health` | GET | Readiness check |
| `/api/model-info` | GET | Model type, training/validation datasets, real metrics |

## Citation

Original work: "AI-Lupira: A Machine Learning-Powered Mobile System for
Lupus Detection and Symptom Analysis" (Misr University for Science and
Technology, 2025).

## Disclaimer

This tool is for research and educational purposes only. It is not a
medical device and should not be used for clinical decision-making.

## License

MIT
