# Algo-Fleet Strategy Brief

## Portfolio Overview
Algo-Fleet allocates capital across three autonomous strategies designed to balance growth and resilience. Capital is assigned by risk bands—10 % high, 30 % medium, 60 % low—and dynamically scales with account equity. A shared risk engine enforces these allocations before orders reach the broker.

## High-Risk Intraday Breakout (10 %)
- **Business Objective:** Capture short-lived momentum bursts in high-beta equities to generate outsized daily returns.
- **Universe:** Liquid tech and growth names (e.g., TSLA, NVDA, AMD, MSFT, QQQ).
- **Approach:** Monitor 5-minute bars for fresh intraday highs above VWAP, paired with ATR-based stops and profit targets delivered via IBKR bracket orders.
- **Edge:** Reactivity to market microstructure and strong trend continuation during high-volume sessions.
- **Risks & Mitigation:** Elevated volatility and gap risk managed by small capital allocation (0.5 % per trade) and tight stop distances.

## Medium-Risk Swing Momentum (30 %)
- **Business Objective:** Harvest multi-day trend continuation in mega-cap equities and thematic ETFs.
- **Universe:** AAPL, AMZN, GOOGL, META, UNG, and similar names.
- **Approach:** Daily timeframe EMA (20/50) crossovers combined with 10-day breakout confirmation; ATR sets stops/takes, risked capital ≈1 % per trade.
- **Edge:** Participates in medium-term momentum while filtering noise via moving averages and breakout confirmation.
- **Risks & Mitigation:** Overnight gaps and trend reversals countered by diversified basket and disciplined exit rules.

## Low-Risk Passive Allocation (60 %)
- **Business Objective:** Provide stable baseline returns through diversified ETF holdings that cushion drawdowns in higher-risk layers.
- **Universe:** VOO, VXUS, TLT, GLD, SHY (configurable mix of equity, international, bonds, and hedges).
- **Approach:** Weekly or event-driven rebalance toward target weights; trades executed with market orders, size scaled to equity.
- **Edge:** Strategic beta exposure with low turnover, ensuring capital preservation and reducing portfolio volatility.
- **Risks & Mitigation:** Market-wide drawdowns mitigated by cross-asset diversification and periodic rebalancing discipline.

## Integrated Risk Management
- **Equity-Based Budgeting:** Risk manager retrieves live `NetLiquidation` from IBKR and enforces pre-set allocation ratios, ensuring layer budgets adapt to account performance.
- **Order Guardrails:** Bracket orders and standardized position sizing cap downside per trade; passive layer uses market orders only when deviation from target weights justifies execution.
- **Operational Controls:** Mode switch (`paper`/`live`) across the stack, Dockerized deployment, and environment-based secrets prevent misconfiguration.
- **Data Feedback Loop:** All trades persist to PostgreSQL, enabling ongoing monitoring, post-trade analytics, and future ML model training for anomaly detection and strategy refinement.
- **Run Telemetry:** Each strategy execution writes a `StrategyRun` record (timings, budget, outcome) plus detailed `Trade` entries with signal snapshots, supporting performance drills and continuous improvement.

