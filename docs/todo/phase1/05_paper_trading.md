# Step 05 – Paper Trading Readiness

## Goals
- Validate strategy budgets, execution flow, and logs before live trials.
- Ensure IBKR paper mode works seamlessly.

## Tasks
- ☐ Review layer budgets vs. simulated equity to confirm reasonable position sizes.
- ☐ Run end-to-end simulation with IBKR paper mode (`BROKER_SIMULATED=false`) and document any adjustments.
- ☐ Add smoke tests that mimic paper execution (entry/exit flows, order statuses).
- ☐ Establish monitoring/alerting for paper runs (basic log checks, Slack/email notifications).

## Deliverables
- Checklist + results validating readiness for paper trading.
- Documented procedure to switch between simulated and paper modes safely.
