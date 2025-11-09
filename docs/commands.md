# Algo-Fleet Command Reference

This cheat sheet lists common commands to interact with the Algo-Fleet stack using Docker and `curl`.

## Docker Compose
- Build and start the full stack (API + Postgres):
  ```bash
  docker compose up --build
  ```
- Run database migrations/initialisation:
  ```bash
  docker compose exec api python scripts/seed_db.py
  ```
  (Migrations also run automatically when the API container starts.)
- Execute strategy runners (simulation enabled by default via `BROKER_SIMULATED=true`):
  ```bash
  docker compose exec api python scripts/run_high.py
  docker compose exec api python scripts/run_medium.py
  docker compose exec api python scripts/run_low.py
  ```
- Run a strategy against a real IBKR gateway (requires TWS/IBG running and `BROKER_SIMULATED=false`):
  ```bash
  docker compose exec -e BROKER_SIMULATED=false api python scripts/run_medium.py
  ```
- Open an interactive shell inside the API container:
  ```bash
  docker compose exec api bash
  ```

## Stock Data Fetching
**Three data sources available** (configured via `MARKET_DATA_SOURCE` env var):
- `ibkr` - Interactive Brokers (best for live trading, requires IBKR connection)
- `alphavantage` - Alpha Vantage API (free, 25 req/day, no rate limits within quota)
- `yfinance` - Yahoo Finance (free but has aggressive rate limits)

## Strategy Simulation (No IBKR Account)
- Simulation is enabled by default via `BROKER_SIMULATED=true` in `docker-compose.yml`.
- Change the virtual account size by setting `SIMULATED_EQUITY` (default: 100000).
- Run any strategy while offline; trades are saved with `order_status="simulated"` so you can analyse decisions.
- Example: list the most recent simulated trades after running a strategy.
  ```bash
  docker compose exec api python -c '
  from sqlmodel import select
  from app.main import context
  from app.models import Trade
  async def show():
      async with context.db.session() as session:
        result = await session.execute(select(Trade).order_by(Trade.opened_at.desc()).limit(5))
        for trade in result.scalars():
              print(trade.symbol, trade.strategy, trade.order_status, trade.signal_snapshot)
  import asyncio; asyncio.run(show())
  '
  ```

## GitHub Automation
- Configure git remotes using the new infrastructure helper (reads `env.example` variables):
  ```bash
  docker compose exec api python -c '
  from lib.infrastructure.github import GitHubClient
  client = GitHubClient()
  client.ensure_repository()
  client.ensure_remote()
  print(f"Configured {client.config.remote_name} -> {client.config.sanitized_url()}")
  '
  ```
- Stage, commit, and push changes (requires git available inside the container):
  ```bash
  docker compose exec api python -c "import os
from lib.infrastructure.github import GitHubClient
client = GitHubClient()
branch = os.getenv('GITHUB_BRANCH', 'dev')
client.commit_and_push('chore: automated update', branch=branch)"
  ```
- Run the interactive helper script (executes tests, asks for commit msg, pushes to `GITHUB_BRANCH`, default `dev`):
  ```bash
  python scripts/push_to_github.py
  ```

### Using Market Data Service (Recommended)
- Fetch historical data (uses configured source):
  ```bash
  docker compose exec api python -c '
  from app.services.market_data import fetch_historical_data
  df = fetch_historical_data("AAPL", days=30)
  print(f"✅ Fetched {len(df)} rows")
  print(df.head())
  '
  ```
- Get current price:
  ```bash
  docker compose exec api python -c '
  from app.services.market_data import fetch_current_price
  price = fetch_current_price("AAPL")
  print(f"AAPL: ${price:.2f}")
  '
  ```
- Check configured data source:
  ```bash
  docker compose exec api python -c '
  from app.services.market_data import get_data_source
  print(f"Current source: {get_data_source()}")
  '
  ```
- Override data source (fetch from specific source):
  ```bash
  docker compose exec api python -c '
  from app.services.market_data import fetch_historical_data
  df = fetch_historical_data("AAPL", days=30, source="alphavantage")
  print(df.head())
  '
  ```

### Setup Alpha Vantage (Free, No Rate Limits!)
1. Get free API key: https://www.alphavantage.co/support/#api-key
2. Set in docker-compose.yml:
   ```yaml
   MARKET_DATA_SOURCE: alphavantage
   ALPHA_VANTAGE_API_KEY: YOUR_KEY_HERE
   ```
3. Restart: `docker compose restart api`
4. Test:
   ```bash
   docker compose exec api python -c '
   from app.services.market_data import fetch_current_price
   print(f"AAPL: ${fetch_current_price('AAPL'):.2f}")
   '
   ```

### Legacy Methods (Direct yfinance)
- Direct yfinance (has rate limits):
  ```bash
  docker compose exec api python -c "import yfinance as yf; data = yf.download('AAPL', period='1mo', progress=False); print(data.tail())"
  ```
- Test data tools (Polars + DuckDB):
  ```bash
  docker compose exec api python -c "
  import polars as pl
  print(f'✅ Polars: {pl.__version__}')
  df = pl.DataFrame({'symbol': ['AAPL'], 'price': [150.0]})
  print(df)
  "
  ```
- Fetch real-time quote:
  ```bash
  docker compose exec api python -c "
  import yfinance as yf
  ticker = yf.Ticker('AAPL')
  info = ticker.info
  print(f\"Symbol: {info.get('symbol')}\")
  print(f\"Price: \${info.get('currentPrice')}\")
  print(f\"Day High: \${info.get('dayHigh')}\")
  print(f\"Day Low: \${info.get('dayLow')}\")
  print(f\"Volume: {info.get('volume'):,}\")
  "
  ```
- Bulk fetch for strategy universe:
  ```bash
  docker compose exec api python -c "
  import yfinance as yf
  symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA']
  for symbol in symbols:
      ticker = yf.Ticker(symbol)
      price = ticker.info.get('currentPrice', 'N/A')
      print(f'{symbol}: \${price}')
  "
  ```

## IBKR Connectivity Check
- Confirm the API container reaches the IBKR gateway:
  ```bash
  docker compose exec api python -c "from app.core.broker_client import BrokerClient; from app.config import get_settings; s=get_settings(); c=BrokerClient(settings=s); c.connect(); print('✅ Connected to IBKR'); c.disconnect()"
  ```

## REST API (curl)
- Health probe:
  ```bash
  curl http://localhost:8000/health
  ```
- List all recorded trades:
  ```bash
  curl http://localhost:8000/trades
  ```
- Filter trades by strategy:
  ```bash
  curl "http://localhost:8000/trades?strategy=medium_swing&limit=20"
  ```
- Inspect recent strategy runs:
  ```bash
  curl http://localhost:8000/strategy-runs
  ```
- Fetch summary counts (example using `jq` for readability):
  ```bash
  curl -s http://localhost:8000/trades | jq 'group_by(.strategy) | map({strategy: .[0].strategy, trades: length})'
  ```
- Root welcome message:
  ```bash
  curl http://localhost:8000/
  ```

## Database Operations
- Connect to Postgres via psql (inside container):
  ```bash
  docker compose exec db psql -U ${POSTGRES_USER} -d ${POSTGRES_DB}
  ```
- Inspect recent trades directly in SQL:
  ```bash
  docker compose exec db psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "SELECT symbol, strategy, layer, entry_price, opened_at FROM trade ORDER BY opened_at DESC LIMIT 10;"
  ```
- Run Alembic migrations manually (if needed):
  ```bash
  docker compose exec api alembic upgrade head
  ```
- Export trades to CSV using `COPY`:
  ```bash
  docker compose exec db psql -U ${POSTGRES_USER} -d ${POSTGRES_DB} -c "\\COPY trade TO '/var/lib/postgresql/data/trades.csv' CSV HEADER"
  ```

## Local Development Without Docker
- Install dependencies (requires Python ≥3.11):
  ```bash
  python -m venv .venv
  .\.venv\Scripts\activate  # Windows
  source .venv/bin/activate # macOS/Linux
  pip install -r requirements.txt
  uvicorn app.main:app --reload
  ```

## Logs & Monitoring
- Tail API logs:
  ```bash
  docker compose logs -f api
  ```
- Tail only the latest 50 API log lines:
  ```bash
  docker compose logs --tail 50 api
  ```
- Tail Postgres logs:
  ```bash
  docker compose logs -f db
  ```
- Stream both services with timestamps:
  ```bash
  docker compose logs -f --timestamps
  ```

