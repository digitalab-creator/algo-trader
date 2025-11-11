python apps/backtesting/cli/run_backtest.py \
  --strategy medium_swing_v1 \
  --symbols AAPL,MSFT,NVDA \
  --start 2023-01-01 \
  --end 2024-01-01 \
  --params '{"ema_fast":30,"ema_slow":60,"breakout_lookback":10,"stop_atr_multiple":1.0,"take_atr_multiple":3.0}' \
  --initial-capital 200000 \
  --show-trades
