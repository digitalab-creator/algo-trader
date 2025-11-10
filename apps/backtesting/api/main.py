"""Backtesting API entrypoint"""

from __future__ import annotations

from fastapi import FastAPI

from apps.backtesting.api.routes.backtests import router as backtests_router

app = FastAPI(title="Backtesting Service", version="1.0.0")

app.include_router(backtests_router)


@app.get("/health")
def health() -> dict:
    return {"success": True, "data": {"status": "ok", "service": "backtesting"}}
