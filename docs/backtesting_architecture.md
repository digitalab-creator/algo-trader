# 🏴‍☠️ Algo-Trading Backtesting Architecture

**Inspired by lotto-predictor patterns, praising the FSM for guidance!**

---

## Overview

Build a scalable backtesting engine that can simulate **1+ years** of trading for any strategy+params combination WITHOUT hitting API rate limits. This system will power ML grid searches and help discover the ultimate trading strategies.

---

## Key Requirements (from your points a-f)

### a. **Data Normalization Engine**
Different data sources (IBKR, Alpha Vantage, yfinance) return different schemas:
- IBKR → real-time bars with bid/ask
- Alpha Vantage → JSON with different field names
- yfinance → DataFrame with specific columns

**Solution:** Create `DataNormalizer` that converts all sources to unified schema:
```python
@dataclass
class NormalizedBar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    source: str  # 'ibkr', 'alphavantage', 'yfinance'
```

### b. **Massive Scale (1+ year backtests)**
Like lotto-predictor analyzing hundreds of draws with ThreadPoolExecutor, we'll:
- Cache ALL historical data locally (DuckDB + Parquet)
- Run strategies as pure functions (no I/O in hot path)
- Parallelize backtest runs with ThreadPoolExecutor
- Use TimeSeriesSplit for cross-validation

### c. **Redis/BullMQ for Job Queue**
**Storage decision:**
- Use **Redis** for:
  - Job queue (backtest tasks)
  - Real-time progress tracking
  - Caching intermediate results
  - Distributed locking for parallel runs

**Why Redis over BullMQ:**
- Simpler for MVP (no Node.js dependency)
- Built-in data structures (lists, hashes, sorted sets)
- Already in docker-compose
- Can migrate to BullMQ later if we add Node microservices

### d. **Every Analysis in DB**
Like lotto-predictor's `Prediction` and `PredictionDetail` tables:
```python
# Store EVERY backtest run
class BacktestRun(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    strategy_name: str
    params_hash: str  # MD5 of params JSON
    params_json: dict = Field(sa_column=Column(JSON))
    symbols: list[str] = Field(sa_column=Column(JSON))
    start_date: date
    end_date: date
    total_trades: int
    winning_trades: int
    total_pnl: float
    roi: float
    sharpe_ratio: float | None
    max_drawdown: float | None
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Store EVERY simulated trade
class BacktestTrade(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    backtest_run_id: int = Field(foreign_key="backtestrun.id")
    symbol: str
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    qty: float
    side: str  # 'buy' or 'sell'
    pnl: float
    pnl_percent: float
    exit_reason: str  # 'take_profit', 'stop_loss', 'signal_reversal', 'end_of_period'
    metadata: dict = Field(sa_column=Column(JSON))  # Store indicators, signals, etc.
```

### e. **Storage: Free vs. Israeli High-Tech Experience**

#### **Option 1: Free/Low Budget (for now)**
```yaml
Storage Stack:
  - PostgreSQL (Docker): Main DB for trades, backtest results
  - DuckDB (local files): Analytical queries on historical data
  - Parquet files (./data/cache/): Long-term price history storage
  - Redis (Docker): Job queue, caching, progress tracking
  
Cost: $0 (runs on local machine or Railway free tier)
Pros: Zero cost, full control, runs offline
Cons: Not distributed, limited by single machine
```

#### **Option 2: Israeli High-Tech Experience Stack**
```yaml
Storage Stack:
  - PostgreSQL (Railway/Fly.io): Main DB ($5-10/mo)
  - TimescaleDB extension: Time-series optimization
  - S3/Backblaze B2: Parquet files (~$5/TB/mo)
  - Redis Cloud (250MB free): Job queue
  - Grafana Cloud (free tier): Monitoring dashboards
  
Cost: ~$10-20/mo
Pros: Production-ready, scalable, resume-worthy
Cons: Monthly cost, internet dependency
```

**Recommendation:** Start with **Option 1** (free), migrate to **Option 2** when:
- You have > 10 strategies to test
- You need distributed workers
- You want to showcase cloud-native architecture

### f. **Design Principles**
From lotto-predictor's architecture:
1. **Registry Pattern**: Like `ALGORITHM_REGISTRY`, create `STRATEGY_REGISTRY`
2. **Base Classes**: Like `Algorithm` base class, create `BaseBacktestStrategy`
3. **File-based Cache**: Like `CacheService`, create `MarketDataCache`
4. **Parallel Execution**: Like `ThreadPoolExecutor` in simulation_engine
5. **Result Storage**: Like `Prediction` + `PredictionDetail` tables
6. **Grid Search**: Like `grid_search_lstm.py`, create `grid_search_strategies.py`

---

## Architecture Components

### 1. Data Layer (`libs/data/`)

```
libs/data/
├── __init__.py
├── cache_service.py        # File-based cache (JSON + MD5 keys)
├── normalizer.py            # Multi-source data normalizer
├── repository.py            # Historical data repository (DuckDB + Parquet)
└── ingestion/
    ├── ibkr_ingester.py     # Fetch from IBKR
    ├── alphavantage_ingester.py
    └── yfinance_ingester.py
```

**Key Functions:**
```python
class MarketDataRepository:
    def get_historical_bars(
        self, 
        symbol: str, 
        start: date, 
        end: date, 
        interval: str = "1d",
        source: str = "auto"  # Tries cache → yfinance → alphavantage → ibkr
    ) -> list[NormalizedBar]:
        """Get bars from cache or fetch + cache"""
        
    def cache_symbol(
        self, 
        symbol: str, 
        start: date, 
        end: date, 
        interval: str = "1d"
    ):
        """Pre-cache symbol data for backtesting"""
```

### 2. Strategy Evaluators (`libs/strategies/evaluators/`)

```
libs/strategies/evaluators/
├── __init__.py
├── base.py                  # BaseBacktestStrategy
├── high_intraday.py         # Pure function version
├── medium_swing.py
└── low_passive.py
```

**Pattern (like lotto Algorithm):**
```python
class BaseBacktestStrategy:
    version = "base"
    
    def generate_signals(
        self, 
        bars: list[NormalizedBar], 
        params: dict
    ) -> list[TradeSignal]:
        """Pure function: bars → signals (no I/O, no IBKR)"""
        raise NotImplementedError

# Registry
STRATEGY_REGISTRY = {}

def register_strategy(cls):
    STRATEGY_REGISTRY[cls.version] = cls
    return cls

@register_strategy
class MediumSwingEvaluator(BaseBacktestStrategy):
    version = "medium_swing_v1"
    
    def generate_signals(self, bars, params):
        # Convert bars to DataFrame
        df = pd.DataFrame([asdict(b) for b in bars])
        # Calculate indicators
        df["ema20"] = df["close"].ewm(span=params["ema_fast"]).mean()
        df["ema50"] = df["close"].ewm(span=params["ema_slow"]).mean()
        # Generate signals
        signals = []
        for i in range(1, len(df)):
            if df["ema20"].iloc[i] > df["ema50"].iloc[i] and \
               df["ema20"].iloc[i-1] <= df["ema50"].iloc[i-1]:
                signals.append(TradeSignal(
                    timestamp=df["timestamp"].iloc[i],
                    action="buy",
                    symbol=bars[0].symbol,
                    entry_price=df["close"].iloc[i],
                    stop_loss=df["close"].iloc[i] - params["stop_distance"],
                    take_profit=df["close"].iloc[i] + params["take_distance"]
                ))
        return signals
```

### 3. Backtesting Engine (`libs/backtesting/`)

```
libs/backtesting/
├── __init__.py
├── engine.py                # Main backtest runner
├── executor.py              # Fill simulator (limit/market orders)
├── metrics.py               # P/L, Sharpe, drawdown calculators
├── context.py               # BacktestContext (like SimulationEngine)
└── writer.py                # Save results to DB
```

**Engine Pattern (like SimulationEngine.run_comparison):**
```python
class BacktestEngine:
    def __init__(self, db: Session, redis_client: RedisClient):
        self.db = db
        self.redis = redis_client
        self.repo = MarketDataRepository()
    
    def run_backtest(
        self,
        strategy_name: str,
        params: dict,
        symbols: list[str],
        start_date: date,
        end_date: date,
        initial_capital: float = 100000
    ) -> BacktestRun:
        """Run single backtest"""
        # 1. Load cached data
        all_bars = {}
        for symbol in symbols:
            all_bars[symbol] = self.repo.get_historical_bars(
                symbol, start_date, end_date
            )
        
        # 2. Get strategy evaluator
        strategy_cls = STRATEGY_REGISTRY[strategy_name]
        strategy = strategy_cls()
        
        # 3. Generate signals
        all_signals = []
        for symbol, bars in all_bars.items():
            signals = strategy.generate_signals(bars, params)
            all_signals.extend(signals)
        
        # 4. Simulate fills
        executor = OrderExecutor(initial_capital)
        trades = []
        for signal in sorted(all_signals, key=lambda s: s.timestamp):
            trade = executor.execute_signal(signal, all_bars[signal.symbol])
            if trade:
                trades.append(trade)
        
        # 5. Calculate metrics
        metrics = calculate_metrics(trades, initial_capital)
        
        # 6. Save to DB
        run = BacktestRun(
            strategy_name=strategy_name,
            params_hash=hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest(),
            params_json=params,
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            **metrics
        )
        self.db.add(run)
        self.db.flush()
        
        for trade in trades:
            bt_trade = BacktestTrade(backtest_run_id=run.id, **trade)
            self.db.add(bt_trade)
        
        self.db.commit()
        return run
    
    def run_grid_search(
        self,
        strategy_name: str,
        param_grid: dict,
        symbols: list[str],
        start_date: date,
        end_date: date
    ) -> list[BacktestRun]:
        """Parallel grid search (like SimulationEngine with ThreadPoolExecutor)"""
        param_combinations = list(itertools.product(*param_grid.values()))
        results = []
        
        def run_single(param_values):
            params = dict(zip(param_grid.keys(), param_values))
            with SessionLocal() as session:
                engine = BacktestEngine(session, self.redis)
                return engine.run_backtest(
                    strategy_name, params, symbols, start_date, end_date
                )
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {
                executor.submit(run_single, vals): vals 
                for vals in param_combinations
            }
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                    logger.info(f"Completed backtest: ROI={result.roi:.2%}")
                except Exception as e:
                    logger.error(f"Backtest failed: {e}")
        
        return results
```

### 4. CLI Scripts (`scripts/`)

```bash
# Pre-cache symbols for 1 year
python scripts/cache_symbols.py --symbols AAPL,MSFT,TSLA --start 2023-01-01 --end 2024-01-01

# Run single backtest
python scripts/run_backtest.py \
  --strategy medium_swing_v1 \
  --params '{"ema_fast":20,"ema_slow":50,"stop_distance":5,"take_distance":15}' \
  --symbols AAPL,MSFT \
  --start 2023-01-01 --end 2024-01-01

# Grid search
python scripts/grid_search.py \
  --strategy medium_swing_v1 \
  --config configs/medium_grid.yaml \
  --symbols AAPL,MSFT,GOOGL \
  --start 2023-01-01 --end 2024-01-01
```

**Grid Config (configs/medium_grid.yaml):**
```yaml
strategy: medium_swing_v1
param_grid:
  ema_fast: [10, 20, 30]
  ema_slow: [40, 50, 60]
  stop_distance: [3, 5, 7]
  take_distance: [10, 15, 20]
symbols:
  - AAPL
  - MSFT
  - GOOGL
date_range:
  start: "2023-01-01"
  end: "2024-01-01"
```

### 5. API Endpoints (`app/routes/backtests.py`)

```python
@router.get("/backtests")
def list_backtests(
    strategy: str | None = None,
    min_roi: float | None = None,
    limit: int = 50
):
    """List backtest runs with filters"""
    
@router.get("/backtests/{run_id}")
def get_backtest(run_id: int):
    """Get detailed backtest results"""
    
@router.get("/backtests/{run_id}/trades")
def get_backtest_trades(run_id: int):
    """Get all trades from a backtest run"""
    
@router.get("/backtests/top")
def get_top_strategies(metric: str = "roi", limit: int = 10):
    """Get best performing strategy+params combinations"""
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     1. Data Ingestion                           │
│  yfinance/Alpha Vantage/IBKR → Normalizer → DuckDB + Parquet   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     2. Backtest Execution                       │
│  Strategy Evaluator → Signals → Order Executor → Simulated     │
│  Trades → Metrics Calculator                                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     3. Result Storage                           │
│  BacktestRun + BacktestTrades → PostgreSQL                     │
│  Progress Updates → Redis                                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     4. Analysis & ML                            │
│  Grid Search → Best Params → Feature Engineering → ML Model    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### **Phase 1: Data Foundation** (Week 1)
- [ ] Create `MarketDataRepository` with DuckDB storage
- [ ] Build `DataNormalizer` for multi-source support
- [ ] Implement `MarketDataCache` (file-based, like lotto CacheService)
- [ ] Script to pre-cache 1 year of data for target symbols

### **Phase 2: Backtest Core** (Week 2)
- [ ] Create `BaseBacktestStrategy` and registry
- [ ] Port existing strategies to evaluator pattern (pure functions)
- [ ] Build `OrderExecutor` for simulated fills
- [ ] Implement `BacktestEngine.run_backtest()`
- [ ] Add database models (BacktestRun, BacktestTrade)

### **Phase 3: Grid Search** (Week 3)
- [ ] Implement `BacktestEngine.run_grid_search()` with ThreadPoolExecutor
- [ ] Create grid config YAML parser
- [ ] Add Redis job queue for distributed runs
- [ ] Build CLI scripts (run_backtest.py, grid_search.py)

### **Phase 4: Analysis & API** (Week 4)
- [ ] Add metrics calculation (Sharpe, drawdown, win rate)
- [ ] Create API endpoints for backtest results
- [ ] Build simple HTML dashboard (like lotto email templates)
- [ ] Document best practices and usage examples

---

## Scalability Considerations

### Current (MVP):
- 4 parallel backtest workers (ThreadPoolExecutor)
- 1 year of daily data (~250 bars per symbol)
- 10 symbols = 2,500 bars cached
- Grid search: 3×3×3×3 = 81 parameter combinations
- **Total runtime: ~5-10 minutes for full grid**

### Future (Production):
- Celery workers across multiple machines
- 5 years of minute data (~1.25M bars per symbol)
- 100+ symbols = 125M bars (stored in Parquet, queried via DuckDB)
- ML-driven parameter optimization (Optuna, Ray Tune)
- **Total runtime: Hours, but distributed**

---

## Next Steps

1. **Review this architecture** - Does it match your vision?
2. **Confirm storage choice** - Free local stack or cloud stack?
3. **Choose first strategy** - Which one to backtest first?
4. **Symbol list** - Which stocks/currencies/options to analyze?

Once confirmed, I'll start implementing Phase 1 (Data Foundation) with the cache service and repository pattern from your lotto-predictor repo.

Ready to build, Captain? ⚓️

