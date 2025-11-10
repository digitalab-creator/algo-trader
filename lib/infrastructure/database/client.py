"""
Database client - PostgreSQL + SQLAlchemy wrapper.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


class DatabaseClient:
    """
    PostgreSQL client using SQLAlchemy.

    Provides async session management, connection pooling, and transactions.

    Example:
        ```python
        async with context.db.session() as session:
            result = await session.execute(select(Trade))
            trades = result.scalars().all()
        ```
    """

    def __init__(self, database_url: str | None = None):
        """
        Initialize database client.

        Args:
            database_url: PostgreSQL URL (defaults to DATABASE_URL env var)
        """
        self.database_url = database_url or os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL must be set")

        # Create async engine
        self.engine = create_async_engine(
            self.database_url,
            echo=os.getenv("SQL_ECHO", "false").lower() == "true",
            pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
        )

        # Create session factory
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get a database session.

        Yields:
            AsyncSession for database operations
        """
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def health_check(self) -> bool:
        """Check if database is reachable."""
        try:
            async with self.session() as session:
                await session.execute("SELECT 1")
            return True
        except Exception:
            return False

    async def close(self) -> None:
        """Close database connections."""
        await self.engine.dispose()

