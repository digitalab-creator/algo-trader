# 📋 py-microservice-core - Summary

Complete Python infrastructure package for microservices, similar to the TypeScript `@roi-me/microservice-core`.

---

## 📁 Package Structure

```
py-microservice-core/
├── src/py_microservice_core/
│   ├── __init__.py                    # Main exports
│   ├── bootstrap/
│   │   ├── setup.py                   # ONE FUNCTION setup
│   │   └── context.py                 # MicroserviceContext
│   ├── internal/
│   │   ├── logger/                    # Structured logging + trace IDs
│   │   ├── database/                  # PostgreSQL + SQLAlchemy
│   │   ├── redis_client/              # Redis wrapper
│   │   ├── monitoring/                # Metrics + events
│   │   └── api_clients/               # HTTP clients with retry/cache
│   ├── middleware/
│   │   └── trace.py                   # Trace ID middleware
│   └── validation/
│       ├── startup.py                 # Startup checks
│       └── cli.py                     # CLI validation tool
├── docs/
│   ├── MICROSERVICE_CHECKLIST.md      # How to create new service
│   ├── ALGO_TRADING_INTEGRATION.md    # Integration guide
│   └── ...
├── examples/
│   └── simple_service.py              # Working example
├── tests/                             # Unit tests
├── pyproject.toml                     # Package config
├── README.md                          # Main documentation
├── INSTALL.md                         # Installation guide
└── SUMMARY.md                         # This file
```

---

## ✨ Key Features

### 🎯 ONE FUNCTION Setup
```python
from py_microservice_core import setup_microservice

app, context = setup_microservice(
    service_name="my-service",
    features={"database": True, "redis": True}
)
```

### 🔌 Built-in Infrastructure
- **Database:** PostgreSQL + SQLAlchemy (async)
- **Cache:** Redis with JSON serialization
- **Logging:** Structured logs with trace IDs
- **Monitoring:** Metrics + events (Redis-backed)
- **API Clients:** Retry + circuit breaker + cache
- **Health Checks:** Automatic endpoints

### 📊 Trace ID Propagation
Every log automatically includes:
- `trace_id` - Unique per request chain
- `span_id` - Unique per service hop
- `parent_span_id` - Previous service
- `caller_service` - Who called us

### 🛡️ Validation
- Startup checks (DB, Redis connectivity)
- CLI tool: `validate-microservice`
- Type checking ready (mypy)

---

## 🚀 Usage Example

```python
from fastapi import APIRouter, Depends
from py_microservice_core import setup_microservice
from py_microservice_core.bootstrap.context import MicroserviceContext

# Create router
router = APIRouter(prefix="/api")

@router.get("/users")
async def get_users(context: MicroserviceContext = Depends(get_context)):
    async with context.db.session() as session:
        result = await session.execute(select(User))
        return result.scalars().all()

# Setup (ONE CALL!)
app, context = setup_microservice(
    service_name="user-service",
    port=8000,
    features={"database": True, "redis": True},
    routers=[router]
)
```

That's it! You get:
- ✅ `/health` endpoint
- ✅ `/metrics` endpoint
- ✅ `/docs` (Swagger UI)
- ✅ Trace IDs in all logs
- ✅ DB connection pooling
- ✅ Redis caching
- ✅ Monitoring

---

## 📦 Installation

### Development Mode
```bash
pip install -e path/to/py-microservice-core
```

### From Wheel
```bash
pip install py-microservice-core
```

See [INSTALL.md](./INSTALL.md) for details.

---

## 🔄 Comparison with TypeScript Version

| Feature | TypeScript | Python |
|---------|-----------|--------|
| **Setup Function** | `setupMicroservice()` | `setup_microservice()` |
| **Database** | MariaDB + Knex | PostgreSQL + SQLAlchemy |
| **Cache** | ioredis | redis-py |
| **Framework** | Express | FastAPI |
| **Logging** | Custom | structlog |
| **Trace IDs** | ✅ | ✅ |
| **Monitoring** | ✅ | ✅ |
| **API Clients** | ✅ (axios) | ✅ (httpx) |
| **Validation** | ✅ (CLI) | ✅ (CLI) |
| **Docs** | Swagger | OpenAPI/Swagger |

---

## 📚 Documentation

1. **[README.md](./README.md)** - Overview + quick start
2. **[INSTALL.md](./INSTALL.md)** - Installation guide
3. **[docs/MICROSERVICE_CHECKLIST.md](./docs/MICROSERVICE_CHECKLIST.md)** - Create new service
4. **[docs/ALGO_TRADING_INTEGRATION.md](./docs/ALGO_TRADING_INTEGRATION.md)** - Integration guide
5. **[examples/simple_service.py](./examples/simple_service.py)** - Working example

---

## 🎯 Benefits

### Before
```python
# 200+ lines of boilerplate
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from sqlalchemy import create_engine
# ... 190 more lines
```

### After
```python
# 5 lines!
from py_microservice_core import setup_microservice

app, context = setup_microservice(
    service_name="my-service",
    features={"database": True, "redis": True}
)
```

**Code Reduction: 90%!** 🎉

---

## 🔧 Algo-Trading Integration

Perfect fit for the algo-trading project:

```python
# app/main.py (before: 50+ lines)
from py_microservice_core import setup_microservice
from app.routes import trades_router, strategies_router

app, context = setup_microservice(
    service_name="algo-fleet",
    port=8000,
    features={"database": True, "redis": True},
    routers=[trades_router, strategies_router]
)

# That's it! Replace app/core/db.py, logging setup, etc.
```

See [docs/ALGO_TRADING_INTEGRATION.md](./docs/ALGO_TRADING_INTEGRATION.md) for full migration guide.

---

## 🧪 Testing

```bash
# Run validation
validate-microservice

# Run unit tests
pytest

# Type checking
mypy src/

# Code formatting
black src/ tests/
ruff check src/ tests/
```

---

## 🚢 Deployment

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "-m", "app.main"]
```

### docker-compose.yml
```yaml
services:
  app:
    build: .
    ports: ["8000:8000"]
    environment:
      DATABASE_URL: postgresql+psycopg://user:pass@db:5432/mydb
      REDIS_URL: redis://redis:6379/0
  db:
    image: postgres:16
  redis:
    image: redis:7
```

---

## 📊 Package Info

| Property | Value |
|----------|-------|
| **Name** | py-microservice-core |
| **Version** | 1.0.0 |
| **Python** | ≥3.11 |
| **License** | MIT |
| **Status** | Production-ready |

---

## 🆘 Support

### Quick Validation
```bash
validate-microservice
```

### Check Installation
```python
python -c "from py_microservice_core import setup_microservice; print('✅ OK')"
```

### Get Help
- Read docs in `docs/` directory
- Check examples in `examples/`
- Review source code in `src/`

---

## 🎓 Philosophy

**Opinionated > Flexible**

This package makes strong choices:
- PostgreSQL (not MySQL/MongoDB)
- FastAPI (not Flask/Django)
- SQLAlchemy (not raw SQL)
- Redis (REQUIRED for monitoring)
- Async/await (not sync)

**Why?** Consistency across all services. Less decisions = faster development = fewer bugs.

---

## 🔮 Roadmap

Future enhancements:
- [ ] Queues support (RabbitMQ/Celery)
- [ ] Prometheus metrics export
- [ ] GraphQL support
- [ ] gRPC support
- [ ] Service mesh integration
- [ ] Distributed tracing (OpenTelemetry)

---

## 📜 License

MIT - see LICENSE file

---

**Built with ❤️ for Python microservices**  
**Inspired by @roi-me/microservice-core (TypeScript)**

---

*Version 1.0.0 - November 2025*

