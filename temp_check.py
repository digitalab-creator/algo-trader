from pathlib import Path
import json
from datetime import datetime
from types import SimpleNamespace

from apps.backtesting.strategies.medium_swing import MediumSwingStrategy
from apps.backtesting.engine.executor import simulate_trade, SimulationConfig
from apps.backtesting.engine.portfolio import Portfolio
from apps.backtesting.engine.metrics import calculate_metrics
from apps.backtesting.strategies.utils import bars_to_dataframe

symbols = ['AAPL', 'MSFT', 'NVDA']
params = {
    'ema_fast': 30,
    'ema_slow': 60,
    'breakout_lookback': 10,
    'stop_atr_multiple': 1.0,
    'take_atr_multiple': 3.0,
}

bars_data = {}
for path in Path('data/cache').glob('*.json'):
    data = json.loads(path.read_text())
    meta = data.get('metadata', {})
    sym = meta.get('symbol')
    if sym in symbols and meta.get('start') == '2023-01-01' and meta.get('end') == '2024-01-01' and meta.get('interval') == '1d':
        converted = []
        for row in data['value']:
            converted.append(SimpleNamespace(
                timestamp=datetime.fromisoformat(row['timestamp']),
                open=row['open'],
                high=row['high'],
                low=row['low'],
                close=row['close'],
                volume=row['volume'],
            ))
        bars_data[sym] = converted

missing = set(symbols) - set(bars_data)
if missing:
    print('Missing cache for symbols:', missing)

strategy = MediumSwingStrategy()
signals = []
dfs = {}
for sym, bars in bars_data.items():
    dfs[sym] = bars_to_dataframe(bars)
    signals.extend(strategy.generate_signals(sym, bars, params=params))

signals.sort(key=lambda s: (s.timestamp, s.symbol))

portfolio = Portfolio(200000)
config = SimulationConfig()
trades = []
for signal in signals:
    df = dfs.get(signal.symbol)
    if df is None or df.empty:
        continue
    trade = simulate_trade(signal, df, current_equity=portfolio.current_equity, config=config)
    if trade:
        portfolio.apply_pnl(trade.exit_time, trade.pnl)
        trades.append(trade)

summary = calculate_metrics(
    trades,
    initial_capital=200000,
    final_capital=portfolio.current_equity,
    equity_curve=portfolio.equity_curve,
    execution_time_seconds=0.0,
)

print('Signals generated:', len(signals))
print('Trades executed:', summary.total_trades)
print('Winning trades:', summary.winning_trades)
print('Losing trades:', summary.losing_trades)
print('Win rate:', summary.win_rate)
print('ROI:', summary.roi)
print('Total PnL:', summary.total_pnl)

for trade in trades:
    print(trade.symbol, trade.entry_time.date(), '->', trade.exit_time.date(), f'pnl={trade.pnl:.2f}', trade.exit_reason)
