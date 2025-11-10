"""Initial Algo-Fleet schema.

Revision ID: 20251109_0001
Revises: 
Create Date: 2025-11-09 15:02:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20251109_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "strategyrun",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("strategy", sa.String(), nullable=False),
        sa.Column("layer", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("budget", sa.Float(), nullable=True),
        sa.Column(
            "signals_triggered",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "trades_executed",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index("ix_strategyrun_strategy", "strategyrun", ["strategy"])
    op.create_index("ix_strategyrun_layer", "strategyrun", ["layer"])

    op.create_table(
        "position",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("symbol", sa.String(), nullable=False),
        sa.Column("layer", sa.String(), nullable=False),
        sa.Column("qty", sa.Float(), nullable=False),
        sa.Column("average_price", sa.Float(), nullable=False),
        sa.Column("market_price", sa.Float(), nullable=True),
        sa.Column("market_value", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_position_symbol", "position", ["symbol"])
    op.create_index("ix_position_layer", "position", ["layer"])

    op.create_table(
        "trade",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("symbol", sa.String(), nullable=False),
        sa.Column("layer", sa.String(), nullable=False),
        sa.Column("strategy", sa.String(), nullable=False),
        sa.Column("side", sa.String(), nullable=False),
        sa.Column("qty", sa.Integer(), nullable=False),
        sa.Column("entry_price", sa.Float(), nullable=False),
        sa.Column("exit_price", sa.Float(), nullable=True),
        sa.Column("pnl", sa.Float(), nullable=True),
        sa.Column("budget_allocated", sa.Float(), nullable=True),
        sa.Column("entry_signal", sa.String(), nullable=True),
        sa.Column("exit_signal", sa.String(), nullable=True),
        sa.Column("order_status", sa.String(), nullable=True),
        sa.Column("signal_snapshot", sa.JSON(), nullable=True),
        sa.Column("exit_snapshot", sa.JSON(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("strategy_run_id", sa.Integer(), nullable=True),
        sa.Column(
            "opened_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["strategy_run_id"], ["strategyrun.id"], name="fk_trade_strategyrun"
        ),
    )
    op.create_index("ix_trade_symbol", "trade", ["symbol"])
    op.create_index("ix_trade_layer", "trade", ["layer"])
    op.create_index("ix_trade_strategy", "trade", ["strategy"])
    op.create_index("ix_trade_opened_at", "trade", ["opened_at"])


def downgrade() -> None:
    op.drop_index("ix_trade_opened_at", table_name="trade")
    op.drop_index("ix_trade_strategy", table_name="trade")
    op.drop_index("ix_trade_layer", table_name="trade")
    op.drop_index("ix_trade_symbol", table_name="trade")
    op.drop_table("trade")

    op.drop_index("ix_position_layer", table_name="position")
    op.drop_index("ix_position_symbol", table_name="position")
    op.drop_table("position")

    op.drop_index("ix_strategyrun_layer", table_name="strategyrun")
    op.drop_index("ix_strategyrun_strategy", table_name="strategyrun")
    op.drop_table("strategyrun")

