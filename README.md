# 🏴‍☠️ Algo-Fleet — Trading MVP Blueprint

Algo-Fleet is a modular algo-trading stack that connects to Interactive Brokers (paper + live) and splits capital across three predefined risk layers. This blueprint lets a new engineer spin up the system within a day and scales toward ML-driven extensions.

## 🎯 Core Goals
- Dual-mode IBKR connectivity with a single `MODE` switch (`paper`/`live`).
- Capital allocation: 10 % high-risk intraday, 30 % medium-risk swing, 60 % low-risk passive ETFs.
- Unified trade/position storage in PostgreSQL via SQLModel.
- Data lake foundation for ML using DuckDB + Polars + yfinance.
- FastAPI interface for control & observability, Docker-first deployment.

## 🧱 Tech Stack
| Layer            | Choice                        | Rationale                         |
| ---------------- | ----------------------------- | --------------------------------- |
| API              | FastAPI                       | Async-friendly, well documented   |
| ORM              | SQLModel (SQLAlchemy engine)  | Pydantic models + typing          |
| Broker           | ib_insync                     | Stable IBKR client abstraction    |
| Data             | DuckDB, Polars, yfinance      | Local OLAP + fast dataframe ops   |
| Database         | PostgreSQL                    | Industry standard transactional   |
| Config           | Pydantic Settings + dotenv    | Secure secret management          |
| Containers       | Docker, docker-compose        | Reproducible environment          |
| Scheduling       | cron / Celery (future)        | Strategy automation               |

## 📂 Repository Layout
```
algo-fleet/
  app/
    main.py
    config.py
    core/
      broker_client.py
      db.py
      orders.py
      risk.py
    models/
      trade.py
      position.py
    strategies/
      high_intraday.py
      medium_swing.py
      low_passive.py
    services/
      data_fetcher.py
  scripts/
    run_high.py
    run_medium.py
    run_low.py
    seed_db.py
  data/
    README.md          # placeholder for DuckDB files
  Dockerfile
  docker-compose.yml
  requirements.txt
  .env.example
  PLAN.md
  README.md
```

## ⚙️ Quickstart (Paper Mode)
1. Install Docker & Docker Compose v2.
2. Duplicate `env.example` to `.env` and set credentials (`MODE=paper` for IB paper trading). Include your GitHub repo URL/token if you plan to push from CI.
3. Launch the stack (migrations auto-run on startup):
   ```bash
   docker compose up --build
   ```
4. (Optional) Connect a real IBKR gateway: set `BROKER_SIMULATED=false` and start TWS/IBG.  
   Leave the default `BROKER_SIMULATED=true` to run in fully offline simulation mode using live market data.
5. Trigger a strategy runner (each run is tracked in `StrategyRun` + `Trade` tables):
   ```bash
   docker compose exec api python scripts/run_medium.py
   ```
6. Inspect trades via FastAPI docs at `http://localhost:8000/docs` or query `/trades`.
7. When ready to push code, configure `.env` from `env.example` (including `GITHUB_BRANCH`, default `dev`). The helper will create the branch locally if it doesn’t exist. Then run:
   ```bash
   python scripts/push_to_github.py
   ```

## 🧠 Risk & Strategy Overview
- **High Risk (10 %)** — Intraday breakout, 5-min bars, tight stops, bracket orders.
- **Medium Risk (30 %)** — Swing trading with EMA cross + ATR breakout.
- **Low Risk (60 %)** — Passive ETF allocation with weekly rebalance.

Risk budgets derive from live equity fetched via IB account summary and enforced prior to order submission.

### Deal Tracking & Analytics
- Every execution logs a `StrategyRun` record with timing, budget, and outcome metadata.
- Each order attempt creates a `Trade` record capturing signals, sizing, broker status, and JSON snapshots for deeper analytics.
- Use these tables to aggregate performance by strategy, layer, signal type, and risk budget.

## 📊 Data Layer
- Historical pulls via yfinance, stored in DuckDB under `data/algo.duckdb`.
- Polars DataFrame workflow for fast feature engineering, ready for ML upgrades.

## 🚀 Deployment Targets
- Local: Docker Compose with mounted volume for hot reload.
- Cloud (future): Railway, Fly.io, or GCP Cloud Run; Postgres via managed service.
- CI/CD: GitHub Actions matrix (tests + lint + docker build).

## 🛣 Roadmap Highlights
1. **MVP** — Strategy runners, API, Postgres logging, IBKR paper mode.
2. **v2** — Dashboard (Streamlit/React), Prometheus metrics, alerting.
3. **v3** — Backtesting harness, ML experiments (LightGBM, scikit-learn).
4. **v4** — Automated scheduling, Feature store (Feast), production deployments.

## 📬 Pitch Snippet
> “המערכת שלנו מחלקת סיכונים בזמן אמת בין שלוש אסטרטגיות עצמאיות — ממונפת, סווינג, ופסיבית — כולן רצות דרך IBKR API על תשתית מודולרית מבוססת FastAPI, PostgreSQL ו-Docker, עם Data Lake שמוכן ל-ML.”

## ✅ Next Steps
- Follow `PLAN.md` for phased implementation.
- Track strategy performance using paper trading logs.
- After 4–8 profitable paper weeks, flip `MODE=live` and tighten monitoring.

## 📚 Documentation
- `docs/commands.md` — quick Docker & curl command cheatsheet.
- `docs/strategy.md` — business narrative and risk-alignment for each trading layer.


