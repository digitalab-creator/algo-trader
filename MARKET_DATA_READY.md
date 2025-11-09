# ✅ Market Data Solution Complete!

## 🎉 What Was Added

### New Service: `app/services/market_data.py`
A unified market data service that supports **three data sources** with a single API:

```python
from app.services.market_data import fetch_historical_data, fetch_current_price

# Automatic source selection from env
df = fetch_historical_data("AAPL", days=30)
price = fetch_current_price("AAPL")

# Or force a specific source
df = fetch_historical_data("AAPL", days=30, source="alphavantage")
```

---

## 📊 Data Sources

| Source | Cost | Rate Limits | Setup Time | Best For |
|--------|------|-------------|------------|----------|
| **IBKR** | Free (with account) | None | 10 min | Live trading |
| **Alpha Vantage** | Free | 25 req/day | 2 min | Development |
| **yfinance** | Free | Aggressive | 0 min | Not recommended |

---

## 🚀 Quick Start: Alpha Vantage (RECOMMENDED)

### Why Alpha Vantage?
- ✅ **Free** - No credit card required
- ✅ **Reliable** - 25 requests/day, 5 per minute
- ✅ **Fast setup** - 2 minutes to get started
- ✅ **No rate limit issues** - Unlike yfinance

### Setup (2 minutes)

**Step 1: Get API Key**
Visit: https://www.alphavantage.co/support/#api-key
- Enter your email
- Copy the key

**Step 2: Configure**
Edit `docker-compose.yml`:
```yaml
environment:
  MARKET_DATA_SOURCE: alphavantage
  ALPHA_VANTAGE_API_KEY: YOUR_KEY_HERE  # <-- Paste your key
```

**Step 3: Restart**
```bash
docker compose restart api
```

**Step 4: Test**
```bash
# Check source
docker compose exec api python -c "
from app.services.market_data import get_data_source
print(f'Using: {get_data_source()}')
"

# Fetch price
docker compose exec api python -c "
from app.services.market_data import fetch_current_price
print(f'AAPL: \${fetch_current_price(\"AAPL\"):.2f}')
"

# Fetch historical data
docker compose exec api python -c "
from app.services.market_data import fetch_historical_data
df = fetch_historical_data('AAPL', days=30)
print(f'✅ Fetched {len(df)} rows')
print(df.head())
"
```

---

## 🏦 Using IBKR (For Live Trading)

### Setup
1. Install TWS/IB Gateway
2. Enable API access (File → Global Configuration → API)
3. Configure `docker-compose.yml`:
   ```yaml
   MARKET_DATA_SOURCE: ibkr
   IBKR_PORT: 7497  # 7497=paper, 7496=live
   ```
4. Start TWS before using API

### Test
```bash
docker compose exec api python -c "
from app.services.market_data import fetch_current_price
print(f'AAPL from IBKR: \${fetch_current_price(\"AAPL\"):.2f}')
"
```

---

## 📚 Documentation

- **[Market Data Setup Guide](docs/market_data_setup.md)** - Complete setup instructions
- **[Commands Reference](docs/commands.md)** - All available commands
- **[Strategy Guide](docs/strategy.md)** - Business strategy overview

---

## 🧪 Testing Commands

### Check Current Source
```bash
docker compose exec api python -c "
from app.services.market_data import get_data_source
print(f'Current source: {get_data_source()}')
"
```

### Fetch Single Price
```bash
docker compose exec api python -c "
from app.services.market_data import fetch_current_price
price = fetch_current_price('AAPL')
print(f'AAPL: \${price:.2f}')
"
```

### Fetch Historical Data
```bash
docker compose exec api python -c "
from app.services.market_data import fetch_historical_data
df = fetch_historical_data('AAPL', days=30)
print(f'Rows: {len(df)}')
print(df.head())
"
```

### Multiple Symbols
```bash
docker compose exec api python -c "
from app.services.market_data import fetch_current_price
symbols = ['AAPL', 'MSFT', 'GOOGL']
for sym in symbols:
    price = fetch_current_price(sym)
    print(f'{sym}: \${price:.2f}')
"
```

### Force Specific Source
```bash
docker compose exec api python -c "
from app.services.market_data import fetch_historical_data
# Force Alpha Vantage even if IBKR is configured
df = fetch_historical_data('AAPL', days=7, source='alphavantage')
print(df.head())
"
```

---

## 🔧 Environment Variables

All configured in `docker-compose.yml`:

```yaml
environment:
  # Choose source: ibkr, alphavantage, or yfinance
  MARKET_DATA_SOURCE: alphavantage
  
  # Alpha Vantage (get free key)
  ALPHA_VANTAGE_API_KEY: your_key_here
  
  # IBKR settings
  IBKR_HOST: 127.0.0.1
  IBKR_PORT: 7497  # 7497=paper, 7496=live
  IBKR_CLIENT_ID: 101
```

---

## 🎯 Recommendations

### For Development/Testing
✅ **Use Alpha Vantage**
- Free and reliable
- 25 requests/day is plenty for development
- No setup hassle

### For Offline Simulation
✅ **Use BROKER_SIMULATED**
- Default in `docker-compose.yml` (`BROKER_SIMULATED=true`)
- Adjust `SIMULATED_EQUITY` to change virtual account size
- Strategies store trades with `order_status="simulated"` so you can review decision logs
- Flip to real trading by setting `BROKER_SIMULATED=false` and launching TWS/IBG

### For Paper Trading
✅ **Use IBKR**
- Real-time data
- Practice with real broker
- No rate limits

### For Live Trading
✅ **Use IBKR**
- Only option for actual trading
- Best data quality
- Required for order execution

---

## 💡 Usage in Strategies

```python
from app.services.market_data import fetch_historical_data
import polars as pl

def backtest_strategy(symbol: str):
    # Fetch 60 days of data (uses configured source)
    df = fetch_historical_data(symbol, days=60)
    
    # Calculate indicators
    df = df.with_columns([
        pl.col("Close").rolling_mean(20).alias("SMA20"),
        pl.col("Close").rolling_mean(50).alias("SMA50"),
    ])
    
    # Your strategy logic here...
    return df

# Works with any source - no code changes needed!
df = backtest_strategy("AAPL")
```

---

## 🚨 Troubleshooting

### Alpha Vantage: "API key not set"
```bash
# Check env vars
docker compose exec api python -c "import os; print(os.getenv('ALPHA_VANTAGE_API_KEY'))"

# If None, add to docker-compose.yml and restart
docker compose restart api
```

### IBKR: "Connection refused"
```bash
# Make sure TWS/Gateway is running
# Check port (7497 for paper, 7496 for live)
# Verify API is enabled in TWS settings
```

### yfinance: "429 Too Many Requests"
```bash
# Switch to Alpha Vantage or IBKR!
# Edit docker-compose.yml:
MARKET_DATA_SOURCE: alphavantage
```

---

## ✅ What's Next?

1. ✅ **Get Alpha Vantage key** (2 minutes) → https://www.alphavantage.co/support/#api-key
2. ✅ **Configure & restart** (1 minute)
3. ✅ **Test commands** (2 minutes)
4. ✅ **Build strategies** using `fetch_historical_data()`
5. ✅ **Switch to IBKR** when ready for paper/live trading

---

## 📦 Files Added/Modified

### New Files
- `app/services/market_data.py` - Unified market data service
- `docs/market_data_setup.md` - Complete setup guide
- `MARKET_DATA_READY.md` - This file

### Modified Files
- `docker-compose.yml` - Added data source env vars
- `requirements.txt` - Added `requests` for Alpha Vantage
- `docs/commands.md` - Updated with market data commands

---

## 🎉 Success!

You now have a **production-ready market data system** with:
- ✅ Three data sources (IBKR, Alpha Vantage, yfinance)
- ✅ Single unified API
- ✅ Environment-based configuration
- ✅ No code changes needed to switch sources
- ✅ Free option with no rate limit issues (Alpha Vantage)

**Start coding strategies - the infrastructure is ready!** 🚀

