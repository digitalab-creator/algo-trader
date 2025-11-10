# Backtesting Roadmap (Dashboards, ML Pipelines, Advanced Analytics)

## Phase 1 – Observability & Dashboards (Week 1)
- **Metrics aggregation**: Build SQL views for ROI, win rate, drawdown by strategy/symbol.
- **API enhancements**: Add endpoints `/analytics/roi-trend`, `/analytics/symbol-breakdown`, `/analytics/risk-matrix`.
- **Dashboard MVP**: Stand up Streamlit app in `apps/analytics` visualizing:
  - Time-series equity curves.
  - Heatmap of strategy vs symbol performance.
  - Pareto chart for profit contribution.
- **Alerting hooks**: Integrate Redis pub/sub channel `backtesting.alerts` for anomalies (e.g., ROI < -5%).

## Phase 2 – ML Feature Store & Pipelines (Weeks 2-3)
- **Feature engineering**: Export backtest trades to Parquet with engineered features (rolling ROI, volatility, hit ratio).
- **Feature store**: Use DuckDB + Polars to maintain feature tables (`features.strategy_performance`, `features.symbol_regime`).
- **Training pipeline**:
  - Prepare supervised dataset predicting next-period ROI per strategy/params.
  - Train baseline models (LightGBM, XGBoost) using scikit-learn pipeline in `apps/ml`.
  - Store models + metadata in `/models/backtesting/` with MLflow tracking (local backend first).
- **AutoML hooks**: Wrap training routine with Optuna for hyperparameter optimization; persist best model per strategy bucket.

## Phase 3 – Recommendation & Experimentation (Weeks 4-5)
- **Strategy recommender**: Build service that ranks strategy+parameter combos for given market regime (volatility, trend); expose `/recommendations` API.
- **Experiment runner**: Extend grid search CLI to accept Optuna studies and store results in `experiments` table.
- **Scenario simulation**: Add ability to replay strategies under stress scenarios (2008, 2020) using cached market regimes.
- **User notification loop**: Generate weekly report (PDF/email) summarizing top-performing strategies vs. benchmarks.

## Phase 4 – Deeper Analytics & Forecasting (Weeks 6-7)
- **Profit forecasting**: Train time-series models (Prophet or NeuralProphet) on cumulative PnL to forecast expected drawdown windows.
- **Risk decomposition**: Implement attribution analysis (strategy, symbol, parameter) with waterfall charts.
- **Anomaly detection**: Use isolation forests on trade-level metrics to flag suspicious fills or data anomalies.
- **What-if simulator**: Provide UI sliders (portfolio weights, risk caps) to recompute expected Sharpe/MaxDD using cached metrics.

## Phase 5 – Production Hardening (Weeks 8+) 
- CI pipeline running backtests nightly on latest data; publish dashboards automatically.
- Integrate consented live trading metrics for closed-loop learning (paper vs live gap analysis).
- Horizontal scale grid-search via Celery + worker autoscaling on Railway/Fly.io.
- Document SLOs & add Sentry/Prometheus instrumentation for all analytics services.
