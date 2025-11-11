# Step 03 – Feature Store & ML Pipeline

## Goals
- Extract reusable features from backtests to feed ML models.
- Train predictive models ranking strategy/parameter combos.

## Tasks
- ☐ Build feature extraction scripts (strategies, params, symbol stats, metrics) -> Parquet/DuckDB.
- ☐ Train tree-based models (LightGBM/XGBoost) predicting ROI/drawdown.
- ☐ Version models with metadata (training window, features) under `models/`.
- ☐ Schedule periodic retraining using latest backtest data.

## Deliverables
- Feature store + trained models ready to prioritize promising configurations.
- Documentation on model training/retraining procedures.
