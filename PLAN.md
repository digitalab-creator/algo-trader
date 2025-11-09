## Algo-Fleet MVP — Phased Build Plan

### Phase 0 — Repo Bootstrap (Day 0)
- Initialize git repository, configure pre-commit hooks if desired.
- Add `.env.example` with all required secrets (`IBKR_*`, `MODE`, `DATABASE_URL`).
- Pin base dependencies in `requirements.txt`.
- Create `docker-compose.yml` and base `Dockerfile` (Python 3.11 slim).

### Phase 1 — Core Services (Day 1)
- Implement `app/config.py` with `pydantic` settings loader.
- Set up `app/core/db.py` with `SQLModel` engine + session factory.
- Integrate Alembic migrations (`alembic.ini`, versions) and session helpers.
- Build FastAPI scaffold in `app/main.py` with health endpoint.
- Add `app/models/trade.py` and `app/models/position.py`.
- Create Alembic-style bootstrap script (`scripts/seed_db.py`) or SQLModel `create_all`.

### Phase 2 — Broker & Risk Layer (Day 2)
- Wrap `ib_insync` in `app/core/broker_client.py` with paper/live switch.
- Implement `app/core/risk.py` for equity budget per layer.
- Draft `app/core/orders.py` helper for bracket orders and market rebalances.
- Add settings schema in `config` to hold layer allocations + universes.

### Phase 3 — Strategy Executors (Days 3–4)
- Implement strategies:
  - `high_intraday.py` intraday breakout
  - `medium_swing.py` EMA/ATR breakout
  - `low_passive.py` ETF rebalance
- Add scripts in `scripts/` to run each strategy and composite runner.
- Integrate strategies with risk budget + broker client.

### Phase 4 — Data Layer (Day 4)
- Implement `app/services/data_fetcher.py` with `yfinance`, `DuckDB`, `Polars`.
- Add ingestion pipeline scripts (e.g., `scripts/fetch_history.py`).
- Document data retention and schema.

### Phase 5 — API & Monitoring (Day 5)
- Expand FastAPI with endpoints for trades, positions, status metrics.
- Add logging/metrics hooks (`structlog`, optional Prometheus exporter).
- Integrate error handling and retries for broker API.

### Phase 6 — Deployment Readiness (Day 6)
- Finalize Docker support; ensure `docker compose up` brings API + Postgres.
- Add sample cron/Celery setup for scheduling strategy runs.
- Prepare Railway/Fly.io deployment notes in `README.md`.

### Phase 7 — QA & Next Steps (Day 7)
- Write pytest suite for risk manager, data fetcher, and strategy signals.
- Manual end-to-end test in IBKR paper account; log results in `/docs/`.
- Collect backlog items for v2 dashboard and ML readiness.

> Deliverable: By end of Week 1 the team can spin up the stack via Docker, run strategies against IBKR paper, and persist all trades for analysis.

