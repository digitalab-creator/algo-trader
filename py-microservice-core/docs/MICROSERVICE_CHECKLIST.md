# 📋 Microservice Creation Checklist

Step-by-step guide to create a new Python microservice using `py-microservice-core`.

---

## 🚀 Quick Start (5 minutes)

### 1. Create Project Structure
```bash
mkdir my-service
cd my-service

# Create directories
mkdir -p src/my_service tests alembic/versions

# Create files
touch src/my_service/__init__.py
touch src/my_service/main.py
touch src/my_service/routes.py
touch .env
touch .env.example
```

### 2. Create pyproject.toml
```toml
[project]
name = "my-service"
version = "0.1.0"
requires-python = ">=3.11"

dependencies = [
    "py-microservice-core>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
]
```

### 3. Create .env File
```bash
# Database
DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/mydb

# Redis
REDIS_URL=redis://localhost:6379/0

# Service
SERVICE_NAME=my-service
PORT=8000
LOG_LEVEL=INFO
```

### 4. Create Main Application (src/my_service/main.py)
```python
from py_microservice_core import setup_microservice
from .routes import router

app, context = setup_microservice(
    service_name="my-service",
    port=8000,
    features={
        "database": True,
        "redis": True,
    },
    routers=[router],
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 5. Create Routes (src/my_service/routes.py)
```python
from fastapi import APIRouter
from py_microservice_core.bootstrap.context import MicroserviceContext

router = APIRouter(prefix="/api", tags=["my-service"])

@router.get("/hello")
async def hello():
    return {"message": "Hello from my-service!"}
```

### 6. Install and Run
```bash
# Install dependencies
pip install -e ".[dev]"

# Run service
python -m src.my_service.main

# Or with uvicorn
uvicorn src.my_service.main:app --reload
```

### 7. Test Endpoints
```bash
# Health check
curl http://localhost:8000/health

# Your endpoint
curl http://localhost:8000/api/hello

# API docs
open http://localhost:8000/docs
```

---

## ✅ What You Get Automatically

- ✅ Health endpoint (`/health`)
- ✅ Metrics endpoint (`/metrics`)
- ✅ OpenAPI docs (`/docs`, `/redoc`)
- ✅ Trace ID in all logs
- ✅ Database connection pool
- ✅ Redis client
- ✅ Monitoring/metrics
- ✅ Structured logging

---

## 🔧 Advanced Features

### Add Database Models
```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    email: Mapped[str]
```

### Add Alembic Migrations
```bash
# Initialize Alembic
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Add users table"

# Run migrations
alembic upgrade head
```

### Add API Clients
```python
app, context = setup_microservice(
    service_name="my-service",
    features={
        "database": True,
        "redis": True,
        "api_clients": {
            "user_service": {
                "base_url": "http://users-service:8012",
                "cache_ttl": 300,
            }
        }
    }
)

# Use in routes
@router.get("/users")
async def get_users(context: MicroserviceContext = Depends(get_context)):
    users = await context.api_clients.user_service.get("/users")
    return users
```

---

## 🐳 Docker Setup

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "src.my_service.main"]
```

### docker-compose.yml
```yaml
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+psycopg://user:pass@db:5432/mydb
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - db
      - redis

  db:
    image: postgres:16
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: mydb

  redis:
    image: redis:7
```

---

## ✅ Validation

Run validation before deployment:
```bash
validate-microservice
```

Checks:
- ✅ pyproject.toml valid
- ✅ Dependencies installed
- ✅ Tests exist
- ✅ Environment variables

---

## 📚 Next Steps

1. Read [FEATURE_LIST.md](./FEATURE_LIST.md) for all available features
2. Check [examples/](../examples/) for more code samples
3. Set up CI/CD pipeline
4. Add monitoring/alerting

---

**Happy coding! 🐍⚡**

