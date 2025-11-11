# Step 01 – Scheduler Integration

## Goals
- Automate nightly grid searches and maintenance tasks.
- Warm/clean caches to keep data fresh for simulations.

## Tasks
- ☐ Implement APScheduler/Celery jobs in `apps/scheduler` (nightly grids, cache maintenance).
- ☐ Configure job metadata (frequency, enabled flag, notifications).
- ☐ Log success/failure per job and integrate with alerting (Slack/email).

## Deliverables
- Scheduler service able to run grid searches and housekeeping automatically.
- Monitoring hooks to detect job failures.
