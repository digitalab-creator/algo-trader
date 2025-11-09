# 🤝 Integrating py-microservice-core into Algo-Trading Project

Guide to refactor your algo-trading project to use `py-microservice-core`.

---

## 📋 Current State vs Target

### Current (algo-trading)
```
app/
  main.py          # Manual FastAPI setup
  config.py        # Pydantic settings
  core/
    db.py          # Manual SQLAlchemy setup
    broker_client.py
    risk.py
  models/
    trade.py
    position.py
```

### Target (with py-microservice-core)
```
app/
  main.py          # ONE FUNCTION setup
  routes/          # Split routes
    trades.py
    strategies.py
  models/          # Keep as-is
  config.py        # Simplified
  # core/ → moved to py-microservice-core!
```

---

## 🔄 Migration Steps

### Step 1: Install Package Locally

```bash
cd C:\Users\orshv\Documents\algo-trading\py-microservice-core

# Install in development mode
pip install -e .

# Or build and install
pip install build
python -m build
pip install dist/py_microservice_core-1.0.0-py3-none-any.whl
```

### Step 2: Update algo-trading requirements.txt

```diff
# requirements.txt
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
- pydantic>=2.5.0
- pydantic-settings>=2.1.0
- sqlalchemy>=2.0.0
- alembic>=1.13.0
- psycopg[binary]>=3.1.0
+ py-microservice-core>=1.0.0

# Keep trading-specific deps
ib-insync>=0.9.86
pandas>=2.1.0
...
```

### Step 3: Refactor app/main.py

**Before:**
```python
from fastapi import FastAPI
from app.core.db import get_session
from app.models import Trade

app = FastAPI(title="Algo-Fleet API")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/trades")
def list_trades(session = Depends(get_session)):
    ...
```

**After:**
```python
from py_microservice_core import setup_microservice
from app.routes import trades_router, strategies_router

app, context = setup_microservice(
    service_name="algo-fleet",
    port=8000,
    features={
        "database": True,
        "redis": True,
    },
    routers=[trades_router, strategies_router],
)

# That's it! Health, metrics, logging all automatic!
```

### Step 4: Split Routes

**app/routes/trades.py:**
```python
from fastapi import APIRouter, Depends
from sqlalchemy import select
from py_microservice_core.bootstrap.context import MicroserviceContext

from app.models import Trade

router = APIRouter(prefix="/trades", tags=["trades"])


def get_context() -> MicroserviceContext:
    # Injected by framework
    from app.main import context
    return context


@router.get("/")
async def list_trades(context: MicroserviceContext = Depends(get_context)):
    async with context.db.session() as session:
        result = await session.execute(select(Trade).limit(100))
        return result.scalars().all()
```

### Step 5: Remove Redundant Code

**Delete:**
- `app/core/db.py` → Use `context.db`
- Manual logging setup → Use `py_microservice_core.internal.logger`
- Manual trace ID middleware → Built-in `TraceMiddleware`

**Keep:**
- `app/core/broker_client.py` (IBKR-specific)
- `app/core/risk.py` (trading logic)
- `app/models/` (unchanged)
- `app/strategies/` (unchanged)

### Step 6: Update Strategy Scripts

**scripts/run_medium.py:**
```python
from py_microservice_core.internal.logger import get_logger
from app.main import context
from app.strategies.medium_swing import run_medium

logger = get_logger(__name__)

async def main():
    logger.info("Starting medium swing strategy")
    
    # Use context.db, context.redis from main
    async with context.db.session() as session:
        await run_medium(session, context)
    
    logger.info("Strategy complete")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

---

## 🎯 Benefits

### Before
```python
# app/main.py (50+ lines)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.core.db import init_db, get_session
from app.config import Settings

logging.basicConfig(...)
settings = Settings()
app = FastAPI(...)
app.add_middleware(CORSMiddleware, ...)
# ... 40 more lines
```

### After
```python
# app/main.py (5 lines!)
from py_microservice_core import setup_microservice

app, context = setup_microservice(
    service_name="algo-fleet",
    features={"database": True, "redis": True}
)
```

**Savings: 45 lines → 5 lines (90% reduction!)**

---

## 📊 Feature Mapping

| Current Code | py-microservice-core Equivalent |
|-------------|--------------------------------|
| `app/core/db.py` | `context.db` |
| Manual logging | `get_logger()` + auto trace IDs |
| `get_session()` | `async with context.db.session()` |
| Health endpoint | Auto-included `/health` |
| Manual CORS | Auto-configured middleware |
| Trace ID handling | `TraceMiddleware` (automatic) |

---

## 🔍 Testing Integration

```bash
cd algo-trading

# Install package
pip install -e ../py-microservice-core

# Start services
docker compose up -d

# Test refactored endpoint
curl http://localhost:8000/health
curl http://localhost:8000/trades

# Check logs (trace IDs automatic!)
docker compose logs api --tail 50
```

---

## 🚀 Next Steps

1. ✅ Install py-microservice-core locally
2. ✅ Refactor `app/main.py` to use `setup_microservice()`
3. ✅ Split routes into separate files
4. ✅ Remove redundant infrastructure code
5. ✅ Update strategy scripts to use context
6. ✅ Test all endpoints
7. ✅ Deploy!

---

## 📚 Additional Resources

- [MICROSERVICE_CHECKLIST.md](./MICROSERVICE_CHECKLIST.md)
- [FEATURE_LIST.md](./FEATURE_LIST.md)
- [examples/simple_service.py](../examples/simple_service.py)

---

**Transform 200 lines into 20! 🐍⚡**

