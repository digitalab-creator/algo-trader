# 📚 lib/infrastructure

Shared infrastructure code for the Algo-Fleet application.

---

## 🎯 Purpose

Centralizes all infrastructure concerns (database, logging, monitoring, etc.) in one place, making the main application code cleaner and more focused on trading logic.

---

## 📁 Structure

```
lib/infrastructure/
├── __init__.py           # Main exports
├── setup.py              # setup_app() function
├── context.py            # AppContext class
├── database/             # PostgreSQL + SQLAlchemy
│   ├── __init__.py
│   └── client.py
├── logger/               # Structured logging + trace IDs
│   └── __init__.py
├── redis_client/         # Redis wrapper
│   ├── __init__.py
│   └── client.py
├── monitoring/           # Metrics + events
│   ├── __init__.py
│   └── client.py
└── middleware/           # HTTP middleware
    ├── __init__.py
    └── trace.py
```

---

## 🚀 Usage

### In app/main.py:
```python
from lib.infrastructure import setup_app
from app.routes import trades_router

app, context = setup_app(
    service_name="algo-fleet",
    features={"database": True, "redis": True},
    routers=[trades_router],
)
```

### In routes:
```python
from lib.infrastructure import AppContext

async def list_trades(context: AppContext = Depends(get_context)):
    async with context.db.session() as session:
        result = await session.execute(select(Trade))
        return result.scalars().all()
```

### In scripts:
```python
from lib.infrastructure.logger import get_logger
from app.main import context

logger = get_logger(__name__)

async def main():
    async with context.db.session() as session:
        # Your code here
        pass
```

---

## ✨ Features

### 1. Database Client
- Async PostgreSQL with SQLAlchemy
- Connection pooling
- Auto-commit/rollback
- Health checks

### 2. Redis Client
- Simple get/set/delete operations
- JSON serialization
- TTL support
- Increment/decrement counters

### 3. Structured Logging
- JSON output
- Trace ID propagation
- Context variables
- Automatic timestamps

### 4. Monitoring
- Metrics (counters, gauges)
- Events (business events)
- Redis-backed (survives restarts)

### 5. Trace Middleware
- Auto-generates trace IDs
- Propagates across services
- Included in all logs

---

## 🔧 Configuration

All configured via environment variables:

```bash
# Database
DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/db

# Redis
REDIS_URL=redis://localhost:6379/0

# Optional
SQL_ECHO=false
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
REDIS_MAX_CONNECTIONS=10
```

---

## 📖 API Reference

### setup_app()
```python
def setup_app(
    service_name: str,
    port: int = 8000,
    features: dict = None,
    routers: list = None,
    enable_cors: bool = True,
    log_level: str = "INFO",
) -> tuple[FastAPI, AppContext]:
```

### AppContext
```python
class AppContext:
    service_name: str
    db: DatabaseClient          # PostgreSQL client
    redis: RedisClient          # Redis client
    monitoring: MonitoringClient  # Metrics/events
```

### DatabaseClient
```python
async with db.session() as session:
    result = await session.execute(query)
    return result.scalars().all()
```

### RedisClient
```python
await redis.set("key", {"data": "value"}, ttl=3600)
data = await redis.get("key")
await redis.delete("key")
```

### MonitoringClient
```python
await monitoring.metric("trade.executed", 1)
await monitoring.event("trade.opened", symbol="AAPL", qty=100)
```

---

## 🎓 Best Practices

1. **Always use context.db.session()** - Don't create sessions manually
2. **Use structured logging** - `get_logger(__name__)`
3. **Record metrics** - Track important business events
4. **Let infrastructure handle errors** - Auto-rollback, trace logging

---

## 🔄 Migration from Old Code

### Before:
```python
# app/core/db.py
from sqlmodel import Session, create_engine

# Manual setup...
```

### After:
```python
# Just use context!
from app.main import context

async with context.db.session() as session:
    # Your code
```

---

## 📚 See Also

- [docs/commands.md](../docs/commands.md) - CLI commands
- [docs/strategy.md](../docs/strategy.md) - Trading strategies
- [PLAN.md](../PLAN.md) - Project roadmap

---

**Keep infrastructure simple, consistent, and centralized!** 🚀

