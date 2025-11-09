# Market Data Setup Guide

This guide explains how to configure and use different market data sources.

## 📊 Available Data Sources

| Source | Cost | Rate Limits | Best For | Setup Time |
|--------|------|-------------|----------|------------|
| **IBKR** | Free with account | None (with account) | Live trading + data | 10 min (requires TWS) |
| **Alpha Vantage** | Free | 25 req/day, 5 req/min | Development/testing | 2 min (get API key) |
| **yfinance** | Free | Aggressive, unpredictable | Not recommended | 0 min (pre-installed) |

---

## 🚀 Quick Start: Alpha Vantage (Easiest!)

**Best for immediate testing without IBKR setup.**

### Step 1: Get Free API Key
Visit: https://www.alphavantage.co/support/#api-key
- Enter your email
- Click "GET FREE API KEY"
- Copy the key (looks like: `ABC123XYZ456`)

### Step 2: Configure
Edit `docker-compose.yml`:

```yaml
environment:
  MARKET_DATA_SOURCE: alphavantage
  ALPHA_VANTAGE_API_KEY: YOUR_KEY_HERE  # Replace with your key
```

### Step 3: Restart
```bash
docker compose restart api
```

### Step 4: Test
```bash
# Check source
docker compose exec api python -c "
from app.services.market_data import get_data_source
print(f'Source: {get_data_source()}')
"

# Fetch current price
docker compose exec api python -c "
from app.services.market_data import fetch_current_price
price = fetch_current_price('AAPL')
print(f'AAPL: \${price:.2f}')
"

# Fetch 30 days of data
docker compose exec api python -c "
from app.services.market_data import fetch_historical_data
df = fetch_historical_data('AAPL', days=30)
print(f'✅ Fetched {len(df)} rows')
print(df.head())
"
```

**✅ Done! You now have unlimited access (within 25 req/day quota).**

---

## 🏦 IBKR Setup (For Live Trading)

**Use this when ready to trade with real/paper money.**

### Step 1: Install TWS or IB Gateway
Download from: https://www.interactivebrokers.com/en/trading/tws.php

### Step 2: Enable API Access
1. Open TWS/Gateway
2. Go to: File → Global Configuration → API → Settings
3. Check "Enable ActiveX and Socket Clients"
4. Add `127.0.0.1` to "Trusted IP Addresses"
5. Note the port:
   - **Paper Trading:** 7497
   - **Live Trading:** 7496

### Step 3: Configure
Edit `docker-compose.yml`:

```yaml
environment:
  MARKET_DATA_SOURCE: ibkr
  IBKR_HOST: 127.0.0.1
  IBKR_PORT: 7497  # 7497 for paper, 7496 for live
  IBKR_CLIENT_ID: 101
```

### Step 4: Start TWS/Gateway
Make sure TWS or IB Gateway is running **before** using the API.

### Step 5: Test
```bash
docker compose restart api

docker compose exec api python -c "
from app.services.market_data import fetch_current_price
price = fetch_current_price('AAPL')
print(f'AAPL from IBKR: \${price:.2f}')
"
```

---

## 🛠️ Usage Examples

### Basic Usage

```python
from app.services.market_data import (
    fetch_historical_data,
    fetch_current_price,
    get_data_source,
)

# Check current source
print(f"Using: {get_data_source()}")

# Get current price
price = fetch_current_price("AAPL")
print(f"AAPL: ${price:.2f}")

# Get historical data
df = fetch_historical_data("AAPL", days=30)
print(df.head())
```

### Force Specific Source

```python
from app.services.market_data import fetch_historical_data

# Force Alpha Vantage even if IBKR is configured
df = fetch_historical_data("AAPL", days=30, source="alphavantage")

# Force yfinance (not recommended)
df = fetch_historical_data("AAPL", days=7, source="yfinance")
```

### Multiple Symbols

```python
from app.services.market_data import fetch_current_price

symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]

for symbol in symbols:
    try:
        price = fetch_current_price(symbol)
        print(f"{symbol}: ${price:.2f}")
    except Exception as e:
        print(f"{symbol}: Error - {e}")
```

### Integration with Strategies

```python
from app.services.market_data import fetch_historical_data
import polars as pl

def calculate_signals(symbol: str):
    # Fetch 60 days of data
    df = fetch_historical_data(symbol, days=60)
    
    # Calculate indicators
    df = df.with_columns([
        pl.col("Close").rolling_mean(20).alias("SMA20"),
        pl.col("Close").rolling_mean(50).alias("SMA50"),
    ])
    
    # Generate signals
    latest = df.tail(1)
    if latest["SMA20"][0] > latest["SMA50"][0]:
        return "BUY"
    else:
        return "SELL"

signal = calculate_signals("AAPL")
print(f"Signal: {signal}")
```

---

## 🔧 Troubleshooting

### Alpha Vantage Issues

**Error: "ALPHA_VANTAGE_API_KEY not set"**
- Make sure you added the key to `docker-compose.yml`
- Restart: `docker compose restart api`

**Error: "Too Many Requests" or "Note: Thank you for using Alpha Vantage"**
- You've hit the daily limit (25 requests/day)
- Wait 24 hours or switch to IBKR

### IBKR Issues

**Error: "Connection refused"**
- Make sure TWS/IB Gateway is running
- Check that API access is enabled in TWS settings
- Verify the port (7497 for paper, 7496 for live)

**Error: "Socket not connected"**
- TWS might have timed out
- Restart TWS/Gateway
- Check firewall settings

### yfinance Issues

**Error: "429 Too Many Requests"**
- Yahoo Finance is rate-limiting you
- Switch to Alpha Vantage or IBKR
- This is why yfinance is not recommended!

---

## 📈 Rate Limits Summary

| Source | Limit | Recommendation |
|--------|-------|----------------|
| IBKR | None (with subscription) | Use for production |
| Alpha Vantage | 25 req/day, 5 req/min | Perfect for development |
| yfinance | Unknown (aggressive) | Avoid |

---

## 🎯 Recommendations

### For Development/Testing
✅ **Use Alpha Vantage**
- Free, reliable, predictable limits
- Perfect for testing strategies
- 25 requests/day is enough for development

### For Paper Trading
✅ **Use IBKR**
- Real-time data
- Same interface as live trading
- No rate limits

### For Live Trading
✅ **Use IBKR**
- Only option for actual trading
- Best data quality
- Required for order execution

---

## 🔄 Switching Data Sources

You can switch sources anytime by editing `docker-compose.yml`:

```bash
# Edit docker-compose.yml
# Change MARKET_DATA_SOURCE to: ibkr, alphavantage, or yfinance

# Restart
docker compose restart api

# Verify
docker compose exec api python -c "
from app.services.market_data import get_data_source
print(f'Now using: {get_data_source()}')
"
```

**No code changes needed!** All your strategies will automatically use the new source.

---

## 💡 Pro Tips

1. **Start with Alpha Vantage** - Get coding immediately
2. **Cache aggressively** - Save API calls, respect rate limits
3. **Use IBKR for trading** - Always use real broker data for actual trades
4. **Override in tests** - Force yfinance in unit tests to avoid using quota
5. **Monitor usage** - Track your Alpha Vantage requests to stay within limits

---

## 📝 Next Steps

1. ✅ Get Alpha Vantage API key (2 minutes)
2. ✅ Test market data fetching (5 minutes)
3. ✅ Build your first strategy using `fetch_historical_data()`
4. ✅ Setup IBKR when ready for paper trading
5. ✅ Go live! 🚀

