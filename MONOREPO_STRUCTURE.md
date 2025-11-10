# 🏴‍☠️ Algo-Trading Monorepo Structure

**Domain-driven architecture by business goal, praisin' the FSM!**

---

## Directory Structure

```
algo-trading/
├── apps/                           # Executable applications
│   ├── backtesting/                # Backtesting & simulation engine
│   │   ├── api/                    # FastAPI for backtest results
│   │   ├── engine/                 # Core backtesting logic
│   │   ├── strategies/             # Strategy evaluators (pure functions)
│   │   ├── cli/                    # CLI scripts (run_backtest, grid_search)
│   │   ├── models/                 # SQLModel (BacktestRun, BacktestTrade)
│   │   ├── alembic/                # DB migrations
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── trading/                    # Live trading execution
│   │   ├── api/                    # FastAPI for trade management
│   │   ├── runners/                # Strategy runners (IBKR integration)
│   │   ├── models/                 # SQLModel (Trade, Position, StrategyRun)
│   │   ├── alembic/                # DB migrations
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   └── scheduler/                  # Cron jobs & scheduled tasks
│       ├── main.py                 # APScheduler or Celery
│       ├── jobs/                   # Job definitions
│       ├── Dockerfile
│       └── requirements.txt
│
├── libs/                           # Shared libraries (domain logic)
│   ├── data/                       # Market data management
│   │   ├── cache_service.py        # File-based cache (lotto pattern)
│   │   ├── normalizer.py           # Multi-source data normalizer
│   │   ├── repository.py           # Historical data repo (DuckDB/Parquet)
│   │   └── ingestors/              # Data fetchers (IBKR, Alpha, yfinance)
│   │
│   ├── infrastructure/             # Core infrastructure (existing)
│   │   ├── database/
│   │   ├── redis_client/
│   │   ├── monitoring/
│   │   ├── logger/
│   │   └── github/
│   │
│   └── strategies/                 # Shared strategy logic
│       ├── base.py                 # Base classes
│       ├── indicators.py           # Technical indicators
│       └── risk.py                 # Risk management utilities
│
├── configs/                        # Configuration files
│   ├── strategies/
│   │   ├── high_intraday.yaml
│   │   ├── medium_swing.yaml
│   │   └── low_passive.yaml
│   ├── grid_search/
│   │   ├── medium_grid.yaml
│   │   └── all_strategies_grid.yaml
│   └── symbols/
│       ├── us_stocks.yaml          # Top US stocks
│       ├── crypto.yaml             # Major cryptocurrencies
│       └── forex.yaml              # Forex pairs
│
├── data/                           # Data storage (gitignored)
│   ├── cache/                      # Market data cache
│   ├── parquet/                    # Long-term storage
│   └── duckdb/                     # Analytical DB
│
├── scripts/                        # Utility scripts
│   ├── setup_dbs.py                # Initialize all databases
│   ├── cache_symbols.py            # Pre-cache market data
│   └── analyze_results.py          # Backtest result analysis
│
├── tests/                          # Tests organized by domain
│   ├── backtesting/
│   ├── trading/
│   ├── libs/
│   └── integration/
│
├── docs/                           # Documentation
│   ├── backtesting_architecture.md
│   ├── commands.md
│   ├── strategy.md
│   └── deployment.md
│
├── docker-compose.yml              # All services
├── docker-compose.dev.yml          # Development overrides
├── .env.example
└── README.md
```

---

## Service Breakdown

### 1. **apps/backtesting** (Port 8001)
**Purpose:** Run historical simulations, grid searches, and performance analysis

**Responsibilities:**
- Load cached historical data
- Execute strategies as pure functions
- Simulate order fills
- Calculate metrics (Sharpe, drawdown, ROI)
- Store results in dedicated database
- Expose API for querying backtest results

**Database:** `backtesting_db` (separate from live trading)

**Key Endpoints:**
- `POST /backtests/run` - Run single backtest
- `POST /backtests/grid-search` - Run parameter grid search
- `GET /backtests` - List all backtest runs
- `GET /backtests/{id}/trades` - Get trades from specific run
- `GET /backtests/top` - Get best performing strategies

### 2. **apps/trading** (Port 8000)
**Purpose:** Execute live trades with IBKR

**Responsibilities:**
- Connect to IBKR (paper/live)
- Execute strategy runners with real orders
- Track live positions and P/L
- Risk management
- Trade logging and monitoring

**Database:** `trading_db` (platform_db + business_db pattern)

**Key Endpoints:**
- `GET /health` - Service health
- `GET /trades` - Live trade history
- `GET /positions` - Current positions
- `GET /strategy-runs` - Strategy execution history
- `POST /strategies/{name}/run` - Manually trigger strategy

### 3. **apps/scheduler** (Port 8002)
**Purpose:** Automated task execution

**Responsibilities:**
- Run strategies on schedule (daily/weekly)
- Refresh market data cache
- Generate performance reports
- Execute rebalancing (low-risk ETF layer)
- Send notifications

**Jobs:**
- `daily_high_intraday` - Run at market open
- `weekly_rebalance` - Run Sunday night
- `cache_refresh` - Run overnight
- `performance_report` - Weekly email

### 4. **libs/data**
**Purpose:** Unified market data access layer

**Shared by:** All apps

**Features:**
- Automatic source selection (cache → yfinance → alphavantage → IBKR)
- Data normalization (all sources → NormalizedBar)
- File-based cache with expiration (lotto pattern)
- DuckDB for analytical queries
- Parquet for long-term storage

### 5. **libs/infrastructure**
**Purpose:** Core utilities (existing)

**Already includes:**
- Database client (async PostgreSQL)
- Redis client
- Monitoring & metrics
- Structured logging
- GitHub integration

---

## Database Architecture

### Separate Databases by Domain

```yaml
PostgreSQL Databases:
  backtesting_db:        # Port 5433
    tables:
      - backtest_runs
      - backtest_trades
      - backtest_metrics
    
  trading_db:            # Port 5432 (existing)
    tables:
      - trades
      - positions
      - strategy_runs
```

**Why Separate?**
- Backtesting generates MASSIVE amounts of data (thousands of simulated trades)
- Live trading needs fast writes (low latency)
- Can scale independently (backtest DB on cheaper storage)
- Clear separation of concerns

---

## Symbol Universe (Comprehensive)

### US Stocks (configs/symbols/us_stocks.yaml)
```yaml
# Tech Giants
mega_cap:
  - AAPL   # Apple
  - MSFT   # Microsoft
  - GOOGL  # Google
  - AMZN   # Amazon
  - NVDA   # Nvidia
  - TSLA   # Tesla
  - META   # Meta

# High Volume Movers
high_volume:
  - SPY    # S&P 500 ETF
  - QQQ    # Nasdaq ETF
  - AMD    # AMD
  - NFLX   # Netflix
  - DIS    # Disney
  - BA     # Boeing
  - JPM    # JP Morgan

# Volatility Plays
volatile:
  - GME    # GameStop
  - AMC    # AMC Entertainment
  - PLTR   # Palantir
  - NIO    # Nio
  - RIVN   # Rivian
```

### Crypto (configs/symbols/crypto.yaml)
```yaml
major:
  - BTCUSD  # Bitcoin
  - ETHUSD  # Ethereum
  - SOLUSD  # Solana
  - ADAUSD  # Cardano
  - DOGEUSD # Dogecoin
```

### Forex (configs/symbols/forex.yaml)
```yaml
major_pairs:
  - EUR.USD
  - GBP.USD
  - USD.JPY
  - AUD.USD
```

### ETFs - Low Risk Layer (configs/symbols/etfs.yaml)
```yaml
diversified:
  - SPY    # S&P 500
  - VTI    # Total Stock Market
  - VOO    # Vanguard S&P 500
  - IWM    # Russell 2000
  - EFA    # International
  - AGG    # Bonds
  - GLD    # Gold
```

**Total Universe: ~40 symbols**

---

## Docker Compose Services

```yaml
version: '3.8'

services:
  # Databases
  backtesting-db:
    image: postgres:16
    environment:
      POSTGRES_DB: backtesting_db
      POSTGRES_USER: backtest_user
      POSTGRES_PASSWORD: backtest_pass
    ports:
      - "5433:5432"
    volumes:
      - backtesting_data:/var/lib/postgresql/data

  trading-db:
    image: postgres:16
    environment:
      POSTGRES_DB: trading_db
      POSTGRES_USER: trading_user
      POSTGRES_PASSWORD: trading_pass
    ports:
      - "5432:5432"
    volumes:
      - trading_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  # Applications
  backtesting:
    build:
      context: .
      dockerfile: apps/backtesting/Dockerfile
    ports:
      - "8001:8000"
    volumes:
      - ./apps/backtesting:/app
      - ./libs:/libs
      - ./data:/data
      - ./configs:/configs
    environment:
      - DATABASE_URL=postgresql+psycopg://backtest_user:backtest_pass@backtesting-db:5432/backtesting_db
      - REDIS_URL=redis://redis:6379/0
      - DATA_DIR=/data
    depends_on:
      - backtesting-db
      - redis

  trading:
    build:
      context: .
      dockerfile: apps/trading/Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./apps/trading:/app
      - ./libs:/libs
      - ./configs:/configs
    environment:
      - DATABASE_URL=postgresql+psycopg://trading_user:trading_pass@trading-db:5432/trading_db
      - REDIS_URL=redis://redis:6379/1
      - MODE=paper
      - IBKR_HOST=host.docker.internal
    depends_on:
      - trading-db
      - redis

  scheduler:
    build:
      context: .
      dockerfile: apps/scheduler/Dockerfile
    volumes:
      - ./apps/scheduler:/app
      - ./libs:/libs
      - ./configs:/configs
    environment:
      - BACKTESTING_API=http://backtesting:8000
      - TRADING_API=http://trading:8000
      - REDIS_URL=redis://redis:6379/2
    depends_on:
      - backtesting
      - trading

volumes:
  backtesting_data:
  trading_data:
  redis_data:
```

---

## Deployment Strategy

### Development (Local)
```bash
# Start all services
docker-compose up -d

# Run backtest
docker-compose exec backtesting python cli/run_backtest.py --strategy medium_swing_v1

# Check live trading health
curl http://localhost:8000/health

# Check backtest results
curl http://localhost:8001/backtests
```

### Production (Railway)
```bash
# Deploy each app separately
railway up apps/backtesting
railway up apps/trading
railway up apps/scheduler

# Each gets its own URL:
# backtesting-prod-abc123.railway.app
# trading-prod-def456.railway.app
# scheduler-prod-ghi789.railway.app
```

---

## Migration Path from Current Structure

```bash
# Current → New mapping:
app/                    → apps/trading/
scripts/run_*.py        → apps/trading/runners/
app/strategies/         → Split:
                          - apps/backtesting/strategies/ (evaluators)
                          - apps/trading/runners/ (live execution)
lib/infrastructure/     → libs/infrastructure/ (unchanged)
app/services/           → libs/data/
app/models/             → apps/trading/models/
alembic/                → apps/trading/alembic/
```

---

## Why This Structure?

### 1. **Clear Separation of Concerns**
- Backtesting ≠ Trading (different goals, different data volumes)
- Each app can scale independently
- Clear domain boundaries

### 2. **Shared Logic in libs/**
- `libs/data` → used by both backtesting and trading
- `libs/strategies` → indicators and risk management
- `libs/infrastructure` → database, Redis, logging

### 3. **Easy to Deploy**
- Railway: Deploy each app as separate service
- Local: `docker-compose up` runs everything
- CI/CD: Test each app independently

### 4. **Future Growth**
Easy to add:
- `apps/analytics` - Performance dashboards (Streamlit)
- `apps/ml` - Model training service
- `apps/webhook` - TradingView webhook receiver
- `libs/notifications` - Email/Telegram alerts

---

## Next: Implementation Order

1. ✅ Create monorepo structure
2. 🔄 Move existing code to `apps/trading`
3. 🔄 Build `libs/data` (cache, normalizer, repository)
4. 🔄 Create `apps/backtesting` skeleton
5. 🔄 Implement strategy evaluators
6. 🔄 Build backtesting engine
7. 🔄 Add grid search CLI
8. 🔄 Update docker-compose

**Ready to restructure, Captain?** ⚓️

