# Step 01 – Backtesting Robustness

## Goals
- Guarantee backtests run on accurate historical data (daily + intraday).
- Provide rich metrics (capital usage, trade details) for analysis.

## Tasks
- ✅ Implement chunked intraday fetching with yfinance fallback to Alpha Vantage.
- ✅ Filter cached data to requested date range before reuse.
- ☐ Enrich `BacktestRun` with `budget_used`, `estimated_profit`, and per-trade capital.
- ☐ Store/display number of trades and trade summaries per run (counts, exit reasons, PnL distribution).
- ☐ Expose utility to purge cache and re-run intervals automatically.
- ☐ Add regression tests covering daily vs 5m intervals.

## Deliverables
- Reliable backtest outputs with consistent metrics regardless of timeframe.
- Scripts/logs documenting how to refresh cache and rerun analyses.
