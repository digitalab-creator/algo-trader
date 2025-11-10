# 🚀 Installation Guide

Quick guide to install and use `py-microservice-core`.

---

## 📦 Option 1: Install from PyPI (Future)

```bash
pip install py-microservice-core
```

---

## 🛠️ Option 2: Install from Source (Now)

### Development Mode (Recommended for Testing)
```bash
cd C:\Users\orshv\Documents\algo-trading\py-microservice-core

# Install in editable mode
pip install -e .

# Or with dev dependencies
pip install -e ".[dev]"
```

### Build and Install
```bash
cd C:\Users\orshv\Documents\algo-trading\py-microservice-core

# Install build tools
pip install build

# Build package
python -m build

# Install wheel
pip install dist/py_microservice_core-1.0.0-py3-none-any.whl
```

---

## ✅ Verify Installation

```python
# Test import
python -c "from py_microservice_core import setup_microservice; print('✅ Package installed!')"

# Check version
python -c "import py_microservice_core; print(py_microservice_core.__version__)"

# Run validation tool
validate-microservice
```

---

## 🔧 Configure algo-trading Project

### 1. Update requirements.txt
```bash
cd C:\Users\orshv\Documents\algo-trading

# Add to requirements.txt
echo "py-microservice-core @ file:///C:/Users/orshv/Documents/algo-trading/py-microservice-core" >> requirements.txt

# Install
pip install -r requirements.txt
```

### 2. Or use direct path install
```bash
cd C:\Users\orshv\Documents\algo-trading

# Install from local path
pip install ../py-microservice-core
```

---

## 🐳 Docker Integration

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy local package
COPY py-microservice-core /tmp/py-microservice-core
RUN pip install /tmp/py-microservice-core

# Copy app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "-m", "app.main"]
```

### Or multi-stage build
```dockerfile
# Stage 1: Build package
FROM python:3.11-slim as builder
COPY py-microservice-core /tmp/py-microservice-core
RUN pip wheel --no-deps --wheel-dir /wheels /tmp/py-microservice-core

# Stage 2: Runtime
FROM python:3.11-slim
COPY --from=builder /wheels /wheels
RUN pip install /wheels/*.whl

COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt

CMD ["python", "-m", "app.main"]
```

---

## 🧪 Test Installation

Create a test file:

```python
# test_install.py
from py_microservice_core import setup_microservice
from fastapi import APIRouter

router = APIRouter()

@router.get("/test")
async def test():
    return {"message": "It works!"}

app, context = setup_microservice(
    service_name="test-service",
    port=8000,
    features={"redis": False, "database": False},
    routers=[router],
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

Run it:
```bash
python test_install.py

# Test
curl http://localhost:8000/health
curl http://localhost:8000/test
```

---

## 🔄 Update Package

```bash
cd py-microservice-core

# Pull latest changes (if using git)
git pull

# Reinstall
pip install -e . --force-reinstall
```

---

## 🆘 Troubleshooting

### Import Error
```bash
# Check if installed
pip list | grep py-microservice-core

# Reinstall
pip uninstall py-microservice-core
pip install -e py-microservice-core/
```

### Module Not Found
```bash
# Check Python path
python -c "import sys; print('\n'.join(sys.path))"

# Add to PYTHONPATH (temporary)
export PYTHONPATH="${PYTHONPATH}:C:/Users/orshv/Documents/algo-trading/py-microservice-core/src"
```

### Build Errors
```bash
# Upgrade build tools
pip install --upgrade pip setuptools wheel build

# Clean and rebuild
rm -rf dist/ build/
python -m build
```

---

## 📚 Next Steps

1. ✅ Install package
2. ✅ Read [docs/MICROSERVICE_CHECKLIST.md](./docs/MICROSERVICE_CHECKLIST.md)
3. ✅ Check [examples/simple_service.py](./examples/simple_service.py)
4. ✅ Integrate into algo-trading: [docs/ALGO_TRADING_INTEGRATION.md](./docs/ALGO_TRADING_INTEGRATION.md)

---

**Happy coding! 🐍⚡**

