# Step 02 – Strategy Runner Enhancements

## Goals
- Make simulation/live runners configurable and informative.
- Capture budget usage and projected profit per strategy layer.

## Tasks
- ✅ Support `--budget` overrides in `scripts/run_high/medium/low.py` with summary output.
- ✅ Log simulation totals (capital deployed, estimated profit) for each run.
- ☐ Centralize trade reporting so strategies push summaries to DB + stdout.
- ☐ Add end-to-end tests covering simulated vs live switching (`BROKER_SIMULATED`).
- ☐ Provide CLI flag to export trades to CSV/Parquet for analysis.

## Deliverables
- Strategy runners usable by analysts without code edits.
- Consistent logging + DB records for trades executed per run.
