# Step 03 – Grid Search Enhancements (Phase A)

## Goals
- Extend grid search to explore strategies, symbol groups, and budgets.
- Persist results for historical comparison and future ML ingestion.

## Tasks
- ☐ Update YAML schema to include `strategies`, `symbol_groups`, `risk_mix`, and budget overrides.
- ☐ Implement resume/retry support with job checkpoints.
- ☐ Write results to new tables (`grid_search_runs`, `grid_search_results`, `grid_search_metrics`).
- ☐ Add CLI flag to limit combinations (e.g., top N per symbol) for quick iteration.
- ☐ Generate summary CSV/JSON automatically after each job.

## Deliverables
- Multi-strategy grid search producing persistent results ready for ML pipelines.
- Documentation + examples demonstrating complex grids (per phase/symbol set).
