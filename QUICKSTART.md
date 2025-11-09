# 🚀 Quick Start - Refactored Algo-Fleet

After refactoring to use centralized `lib/infrastructure`.

---

## ⚡ Quick Test (5 minutes)

### 1. Install Dependencies
```bash
cd C:\Users\orshv\Documents\algo-trading

# Install new dependencies (structlog, redis)
pip install -r requirements.txt
```

### 2. Start Services
```bash
# Start Docker (PostgreSQL + Redis)
docker compose up --build -d

# Check containers
docker compose ps
```

### 3. Test Endpoints
```bash
# Health check (now auto-included by lib/infrastructure!)
curl http://localhost:8000/health

# Metrics (also auto-included!)
curl http://localhost:8000/metrics

# List trades
curl http://localhost:8000/trades

# API docs (still works!)
open http://localhost:8000/docs
```

### 4. Check Logs (Now with Trace IDs!)
```bash
# View logs - notice JSON format + trace IDs
docker compose logs api --tail 20

# Follow logs live
docker compose logs -f api
```

---

## 🎯 What Changed?

### Before:
- Manual database setup
- Basic logging
- 56 lines in `app/main.py`

### After:
- Centralized infrastructure in `lib/`
- Structured logging with trace IDs
- 23 lines in `app/main.py` (59% reduction!)

---

## 📁 New File Structure

```
algo-trading/
├── lib/infrastructure/        # NEW: Centralized infra
│   ├── setup.py              # ONE setup function
│   ├── database/
│   ├── logger/
│   ├── redis_client/
│   ├── monitoring/
│   └── middleware/
│
├── app/
│   ├── main.py               # SIMPLIFIED (23 lines!)
│   ├── routes/               # NEW: Split by domain
│   │   └── trades.py
│   └── core/                 # Trading-specific only
│
└── scripts/
    └── run_medium.py         # UPDATED: Uses lib/
```

---

## 🔧 Usage Examples

### Simple Route:
```python
from lib.infrastructure import AppContext
from app.main import context

@router.get("/trades")
async def list_trades(ctx: AppContext = Depends(lambda: context)):
    async with ctx.db.session() as session:
        result = await session.execute(select(Trade))
        return result.scalars().all()
```

### Strategy Script:
```python
from lib.infrastructure.logger import get_logger
from app.main import context

logger = get_logger(__name__)

async def main():
    logger.info("Starting strategy")
    
    async with context.db.session() as session:
        # Your code here
        pass
    
    # Record metrics (Redis-backed!)
    await context.monitoring.metric("strategy.executed", 1)
```

---

## ✨ New Features (Auto-Included!)

1. **Structured Logging**
   - JSON output
   - Trace IDs in every log
   - Automatic timestamps

2. **Auto Endpoints**
   - `/health` - Health check
   - `/metrics` - Redis-backed metrics
   - `/docs` - Swagger UI

3. **Monitoring**
   - Metrics: `await context.monitoring.metric("name", value)`
   - Events: `await context.monitoring.event("type", key=val)`

4. **Redis Support**
   - `await context.redis.set("key", data, ttl=3600)`
   - `data = await context.redis.get("key")`

---

## 🐛 Troubleshooting

### "Module not found: lib.infrastructure"
```bash
# Make sure you're in project root
cd C:\Users\orshv\Documents\algo-trading

# Install dependencies
pip install -r requirements.txt
```

### "DATABASE_URL not set"
```bash
# Check .env file exists
cat .env

# Should have:
DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/algo
REDIS_URL=redis://localhost:6379/0
```

### Port 5432 already in use
```bash
# Stop local Postgres if running
net stop postgresql

# Or change port in docker-compose.yml:
#   ports: ["5433:5432"]
```

---

## 📚 Next Steps

1. **Update remaining scripts:**
   ```bash
   # TODO: Update these like run_medium.py
   scripts/run_high.py
   scripts/run_low.py
   ```

2. **Add more routes:**
   ```bash
   # Create app/routes/strategies.py
   # Register in app/routes/__init__.py
   # Add to routers list in app/main.py
   ```

3. **Explore monitoring:**
   ```bash
   # Record custom metrics
   await context.monitoring.metric("custom.metric", 1)
   
   # Track business events
   await context.monitoring.event("user.action", user_id=123)
   ```

4. **Read documentation:**
   - [lib/README.md](./lib/README.md) - Infrastructure guide
   - [REFACTORING.md](./REFACTORING.md) - What changed
   - [docs/commands.md](./docs/commands.md) - CLI commands

---

## ✅ Checklist

- [ ] Install dependencies (`pip install -r requirements.txt`)
- [ ] Start Docker (`docker compose up -d`)
- [ ] Test /health endpoint
- [ ] Test /trades endpoint
- [ ] Check logs (see trace IDs!)
- [ ] Run strategy (`python scripts/run_medium.py`)
- [ ] Review new structure (`lib/`, `app/routes/`)

---

**Infrastructure is now centralized and production-ready!** 🎉

*Focus on trading logic, not infrastructure.*

