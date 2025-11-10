# Trading Service Roadmap

## Phase 0 – Baseline Extraction (Completed)
- [x] Bridge existing FastAPI app into `apps/trading/api/main.py` so `docker-compose` can point at the new module without breaking legacy paths.
- [x] Document high-level roadmap for full migration.

## Phase 1 – Modularize Service (Week 1)
- [ ] Relocate current `app/` modules into `apps/trading/` (config, routes, models, services).
- [ ] Update imports to use `apps.trading.*` namespace.
- [ ] Align tests and scripts with new layout.

## Phase 2 – Domain Separation (Week 2)
- [ ] Split API routes into `routes/trades.py`, `routes/strategy_runs.py`, `routes/positions.py`.
- [ ] Introduce service layer (order execution, risk checks) calling shared libs.
- [ ] Ensure logging uses `dh_log` and context tracing.

## Phase 3 – Broker Integration Enhancements (Week 3)
- [ ] Finalize broker abstraction with simulation/live switching via env flags.
- [ ] Add retry/backoff + alerting for IBKR connectivity.
- [ ] Persist execution telemetry (latency, fills) for analytics.

## Phase 4 – Observability & Reliability (Weeks 4-5)
- [ ] Expose Prometheus metrics (orders placed, fails, latencies).
- [ ] Add feature flags for strategy toggles.
- [ ] Implement circuit breakers and throttling per strategy.

## Phase 5 – Automation & QA
- [ ] Create integration tests that simulate end-to-end paper trades.
- [ ] Build smoke test script for deployment validation.
- [ ] Document runbooks and deployment SOPs.
