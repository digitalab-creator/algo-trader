"""FastAPI dependencies for backtesting API"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from fastapi import Depends
from sqlmodel import Session

from apps.backtesting.db import get_session


def get_db_session() -> Generator[Session, None, None]:
    session = get_session()
    try:
        yield session
    finally:
        session.close()
