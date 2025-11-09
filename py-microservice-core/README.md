# 🐍 py-microservice-core

**The ONE FUNCTION to rule all Python microservices!**

*Consolidated infrastructure package - FastAPI, PostgreSQL, Redis, and monitoring in one place!*

---

## 🎯 What Is This?

A **battle-tested** Python microservice infrastructure package that provides:
- ✅ **ONE function setup** (`setup_microservice()`)
- ✅ **90% less code** per service
- ✅ **100% consistency** across all services
- ✅ **Production-ready** infrastructure
- ✅ **Enforced standards** via validation

**Before:** 200-500 lines of boilerplate  
**After:** 20-50 lines total  
**Reduction:** 90%! 🎉

---

## 🚀 Quick Start

### Install
```bash
pip install py-microservice-core
```

### Create a New Microservice (30 lines!)
```python
from py_microservice_core import setup_microservice
from .routes import router

app, context = setup_microservice(
    service_name="my-service",
    port=8000,
    
    features={
        "database": True,      # PostgreSQL + SQLAlchemy
        "redis": True,         # redis-py (REQUIRED!)
        "api_clients": {
            "user_service": {
                "base_url": "http://users-service:8012",
                "cache_strategy": "fallback",
                "cache_ttl": 300
            }
        }
    },
    
    routers=[router]
)

# Use context in routes:
# context.db, context.redis, context.api_clients, context.monitoring
```

**That's it!** You get health checks, monitoring, tracing, validation, and more! ✅

---

## ✨ What You Get Automatically

### Infrastructure
- ✅ FastAPI server (auto-configured with middleware)
- ✅ Database (PostgreSQL + SQLAlchemy + Alembic)
- ✅ Redis (redis-py with opinionated methods)
- ✅ API Clients (circuit breaker, retry, cache strategies)

### Monitoring & Observability
- ✅ **Trace ID propagation** (100% coverage!)
- ✅ **Structured logging** (structlog + JSON)
- ✅ **Metrics persistence** (Redis-backed)
- ✅ **Health endpoints** (/health, /metrics)
- ✅ **Database/Redis monitors**

### Documentation
- ✅ **OpenAPI/Swagger** at `/docs` (automatic!)
- ✅ **ReDoc** at `/redoc`

### Quality Enforcement
- ✅ **Validation** (startup checks)
- ✅ **Type checking** (mypy)
- ✅ **Code formatting** (black + ruff)
- ✅ **Testing framework** (pytest)

---

## 📚 Documentation

### For Developers (START HERE! 👇)
- **[docs/MICROSERVICE_CHECKLIST.md](./docs/MICROSERVICE_CHECKLIST.md)** - Create new microservice
- **[docs/MIGRATION_GUIDE.md](./docs/MIGRATION_GUIDE.md)** - Migrate existing service
- **[docs/FEATURE_LIST.md](./docs/FEATURE_LIST.md)** - Complete API reference

---

## 🔥 Key Features

### 1. Trace ID Propagation (100% Coverage!)
Every log automatically includes:
- `trace_id` - Unique per request chain
- `span_id` - Unique per service hop
- `parent_span_id` - Previous service in chain
- `caller_service` - Who called us

**Follow requests across ALL microservices!**

### 2. Opinionated Interfaces
- **Database:** Consistent session management + migrations
- **Redis:** Simple get/set/delete with TTL
- **API Clients:** Built-in retry, circuit breaker, caching

**Clean & simple!**

### 3. Validation (Blocks Bad Code!)
Validates:
1. pyproject.toml (dependencies)
2. Environment variables (.env)
3. Database migrations
4. Redis connection
5. Tests exist and pass

**Runs before deployment!**

---

## 📦 Full Feature List

### Database Context
```python
# Session management
async with context.db.session() as session:
    result = await session.execute(select(User))
    users = result.scalars().all()

# Migrations handled by Alembic
```

### Redis Context
```python
await context.redis.get("key")
await context.redis.set("key", value, ttl=3600)
await context.redis.delete("key")
await context.redis.exists("key")
await context.redis.increment("counter")
```

### API Clients
```python
result = await context.api_clients.user_service.get("/users")
# Auto: circuit breaker, retry, cache, trace injection!
```

### Monitoring
```python
context.monitoring.metric("operation.count", 1)
context.monitoring.event("user.created", user_id=123)
```

---

## 🔒 Enforcement & Security

### Trace ID (MANDATORY!)
- ❌ Throws error if API call without trace context
- ✅ 100% of logs have trace ID
- ✅ Propagates across all microservices

### Redis (MANDATORY!)
- ❌ Throws error if monitoring without Redis
- ✅ Auto-enabled for all microservices
- ✅ Required for metrics persistence

### Validation
- ❌ Blocks if tests missing/fail
- ❌ Blocks if migrations broken
- ✅ All checks run before deployment

---

## 📊 Package Statistics

| Metric | Value |
|--------|-------|
| **Version** | 1.0.0 |
| **Setup Lines** | 20-50 (vs 200-500 before) |
| **Type Coverage** | 100% ✅ |
| **Build Status** | ✅ Production-ready |
| **Code Reduction** | 70-90% |

---

## 🆘 Support

### Quick Help
```bash
# Validate your service
validate-microservice

# Run tests
pytest

# Format code
black src/ tests/
ruff check src/ tests/
```

---

## 📜 License

MIT

---

**May the code be with you! 🐍⚡**

*Version 1.0.0 - Initial release - November 2025*

