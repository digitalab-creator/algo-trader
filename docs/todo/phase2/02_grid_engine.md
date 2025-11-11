# Step 02 – Grid Search Orchestration

## Goals
- Manage grid search jobs reliably with retries and logging.
- Support risk-mix and portfolio evaluation across strategies.

## Tasks
- ☐ Build `GridSearchEngine` coordinating job queue, retries, structured logging.
- ☐ Add risk-blend evaluation (weighted strategy mixes, Monte Carlo scenarios).
- ☐ Persist job metadata + metrics for auditing and dashboarding.

## Deliverables
- Robust orchestration layer that can queue/rerun grids without manual intervention.
- Stored metrics enabling long-term performance comparisons.
