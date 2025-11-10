# Scheduler Service Roadmap

## Phase 0 – Baseline Setup (Completed)
- [x] Document scheduler roadmap.
- [x] Create service skeleton `apps/scheduler/main.py` to host future jobs.

## Phase 1 – Job Infrastructure (Week 1)
- [ ] Choose orchestration library (APScheduler vs Celery worker) based on resource needs.
- [ ] Implement job registry with metadata (frequency, description, enabled flag).
- [ ] Wire Redis/DB clients via `libs/infrastructure` context.

## Phase 2 – Core Jobs (Week 2)
- [ ] Nightly data cache refresh (pre-fetch historical bars by symbol list).
- [ ] Scheduled strategy runs (high intraday during market hours, medium/low at close).
- [ ] Reconciliation job to compare simulated vs live trades.

## Phase 3 – Monitoring & Alerting (Week 3)
- [ ] Emit metrics per job (duration, success/fail counts).
- [ ] Integrate alerting (Redis pub/sub or email) on failures.
- [ ] Build job dashboard (reuse backtesting analytics UI).

## Phase 4 – Advanced Automation (Weeks 4-5)
- [ ] Add parameter sweep scheduling (kick off grid searches nightly).
- [ ] Implement maintenance tasks (cache cleanup, archive old logs).
- [ ] Provide REST/CLI interface to enable/disable jobs dynamically.
