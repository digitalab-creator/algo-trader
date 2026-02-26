from __future__ import annotations

import re
from pathlib import Path

import duckdb
import polars as pl
import yfinance as yf

DATA_PATH = Path("data")
DATA_PATH.mkdir(parents=True, exist_ok=True)
DUCKDB_PATH = DATA_PATH / "algo.duckdb"

# Only allow safe table names (internal use; avoid injection if table_name ever came from user input)
_TABLE_NAME_ALLOWLIST = re.compile(r"^[a-zA-Z0-9_]+$")


def fetch_yfinance(symbol: str, period_days: int = 365, interval: str = "1d") -> pl.DataFrame:
    raw = yf.download(
        symbol,
        period=f"{period_days}d",
        interval=interval,
        progress=False,
        auto_adjust=False,
    )
    df = pl.from_pandas(raw.reset_index())
    return df.rename({"Date": "date"})


def store_duckdb(df: pl.DataFrame, table_name: str) -> None:
    if not _TABLE_NAME_ALLOWLIST.match(table_name):
        raise ValueError(f"Invalid table name: {table_name!r}")
    with duckdb.connect(str(DUCKDB_PATH)) as con:
        con.register("df", df)
        con.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {table_name} AS
            SELECT * FROM df
            """
        )
        con.execute(
            f"""
            INSERT INTO {table_name}
            SELECT * FROM df
            """
        )

