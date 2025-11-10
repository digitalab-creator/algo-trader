"""Trading service FastAPI entrypoint"""

from app.main import app  # Re-export existing application until full migration

__all__ = ["app"]
