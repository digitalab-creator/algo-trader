# Algo-Fleet

A modular algorithmic trading stack that connects to Interactive Brokers (paper or live) and allocates capital across three risk layers: high-risk intraday, medium-risk swing, and low-risk passive ETFs. Trades and positions are stored in PostgreSQL. Market data is stored in DuckDB for analysis.

## What it does

- Connects to Interactive Brokers via a single mode switch (paper or live).
- Splits capital: 10% high-risk intraday, 30% medium-risk swing, 60% low-risk passive ETFs.
- Stores trades and strategy runs in PostgreSQL (SQLModel).
- Fetches and stores historical data in DuckDB using Polars and yfinance.
- Exposes a FastAPI API for control and inspection.

## Tech stack

- **API:** FastAPI
- **Database:** PostgreSQL, SQLModel
- **Data:** DuckDB, Polars, yfinance
- **Broker:** ib_insync (Interactive Brokers)
- **Deployment:** Docker, docker-compose

## Repository layout

- `app/` — FastAPI app, config, routes, strategies (high_intraday, medium_swing, low_passive), core (broker_client, orders, risk), models (trade, strategy_run), services (data_fetcher, market_data)
- `lib/` — Shared infrastructure (database client, Redis, logging, middleware)
- `scripts/` — run_high.py, run_medium.py, run_low.py, seed_db.py
- `data/` — DuckDB files (e.g. algo.duckdb)
- `env.example` — Copy to `.env` and set your credentials

## How to use

1. Install Docker and Docker Compose v2.
2. Copy `env.example` to `.env`. Set `DATABASE_URL`, and for IB paper trading set `MODE=paper`. Use `BROKER_SIMULATED=true` to run without a live broker connection.
3. Start the stack (migrations run on startup):
   ```bash
   docker compose up --build
   ```
4. Optional: connect a real IBKR gateway (TWS or IB Gateway). Set `BROKER_SIMULATED=false` and configure host/port in `.env`.
5. Run a strategy (e.g. medium-risk swing). Each run is stored as a `StrategyRun` with related `Trade` records:
   ```bash
   docker compose exec api python scripts/run_medium.py
   ```
6. Open the API docs at `http://localhost:8000/docs` or call `GET /trades` to inspect trades.

## Strategy overview

- **High risk (10%)** — Intraday breakout, 5-min bars, bracket orders.
- **Medium risk (30%)** — Swing trading with EMA cross and ATR breakout.
- **Low risk (60%)** — Passive ETF allocation with weekly rebalance.

Risk limits use equity from the IB account summary and are applied before sending orders.

## Data layer

Historical data is pulled via yfinance and stored in DuckDB under `data/algo.duckdb`. Use Polars for feature work and further analysis.

## Documentation

- `docs/commands.md` — Docker and curl command reference.
- `docs/strategy.md` — Strategy and risk description.
