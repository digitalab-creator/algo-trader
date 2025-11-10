"""create backtesting tables

Revision ID: 20251110_0001
Revises: 
Create Date: 2025-11-10 14:36:00.000000

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlmodel import Column, JSON


revision = "20251110_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "backtest_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("strategy_name", sa.String(length=128), nullable=False),
        sa.Column("strategy_version", sa.String(length=32), nullable=False),
        sa.Column("params_hash", sa.String(length=128), nullable=False),
        Column("params_json", JSON, nullable=False),
        Column("symbols", JSON, nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("interval", sa.String(length=16), nullable=False),
        sa.Column("total_trades", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("winning_trades", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("losing_trades", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("initial_capital", sa.Float(), nullable=False),
        sa.Column("final_capital", sa.Float(), nullable=False),
        sa.Column("total_pnl", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("roi", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("sharpe_ratio", sa.Float(), nullable=True),
        sa.Column("max_drawdown", sa.Float(), nullable=True),
        sa.Column("max_drawdown_duration", sa.Integer(), nullable=True),
        sa.Column("win_rate", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("avg_win", sa.Float(), nullable=True),
        sa.Column("avg_loss", sa.Float(), nullable=True),
        sa.Column("profit_factor", sa.Float(), nullable=True),
        sa.Column("execution_time_seconds", sa.Float(), nullable=True),
        sa.Column("data_source", sa.String(length=16), nullable=False, server_default=sa.text("'auto'")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("notes", sa.String(), nullable=True),
    )

    op.create_index("ix_backtest_runs_params_hash", "backtest_runs", ["params_hash"])
    op.create_index("ix_backtest_runs_roi", "backtest_runs", ["roi"])

    op.create_table(
        "backtest_trades",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("backtest_run_id", sa.Integer(), sa.ForeignKey("backtest_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("symbol", sa.String(length=32), nullable=False),
        sa.Column("entry_time", sa.DateTime(), nullable=False),
        sa.Column("exit_time", sa.DateTime(), nullable=False),
        sa.Column("entry_price", sa.Float(), nullable=False),
        sa.Column("entry_signal", sa.String(length=64), nullable=True),
        sa.Column("exit_price", sa.Float(), nullable=False),
        sa.Column("exit_signal", sa.String(length=64), nullable=True),
        sa.Column("exit_reason", sa.String(length=32), nullable=False),
        sa.Column("side", sa.String(length=8), nullable=False),
        sa.Column("qty", sa.Float(), nullable=False),
        sa.Column("pnl", sa.Float(), nullable=False),
        sa.Column("pnl_percent", sa.Float(), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=False),
        sa.Column("stop_loss", sa.Float(), nullable=True),
        sa.Column("take_profit", sa.Float(), nullable=True),
        sa.Column("risk_amount", sa.Float(), nullable=True),
        sa.Column("risk_percent", sa.Float(), nullable=True),
        sa.Column("commission", sa.Float(), nullable=False, server_default=sa.text("0")),
        sa.Column("slippage", sa.Float(), nullable=False, server_default=sa.text("0")),
        Column("details", JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    op.create_index("ix_backtest_trades_symbol", "backtest_trades", ["symbol"])
    op.create_index("ix_backtest_trades_backtest_run_id", "backtest_trades", ["backtest_run_id"])


def downgrade() -> None:
    op.drop_index("ix_backtest_trades_backtest_run_id", table_name="backtest_trades")
    op.drop_index("ix_backtest_trades_symbol", table_name="backtest_trades")
    op.drop_table("backtest_trades")

    op.drop_index("ix_backtest_runs_roi", table_name="backtest_runs")
    op.drop_index("ix_backtest_runs_params_hash", table_name="backtest_runs")
    op.drop_table("backtest_runs")
