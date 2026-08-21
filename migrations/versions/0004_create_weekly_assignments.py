"""create weekly_cycles and assignments tables

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: Union[str, Sequence[str], None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "weekly_cycles",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("cycle_key", sa.Date(), nullable=False, unique=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("associated_draw_no", sa.SmallInteger(), nullable=True),
        sa.ForeignKeyConstraint(["associated_draw_no"], ["draws.draw_no"]),
    )

    op.create_table(
        "assignments",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("weekly_cycle_id", sa.Integer(), nullable=False),
        sa.Column("member_id", sa.Integer(), nullable=False),
        sa.Column("combination_id", sa.Integer(), nullable=False),
        sa.Column(
            "assigned_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["weekly_cycle_id"], ["weekly_cycles.id"]),
        sa.ForeignKeyConstraint(["member_id"], ["members.id"]),
        sa.ForeignKeyConstraint(["combination_id"], ["combination_pool.id"]),
        sa.UniqueConstraint(
            "weekly_cycle_id", "combination_id", name="uq_assignment_no_overlap"
        ),
    )
    op.create_index(
        "ix_assignments_cycle_member", "assignments", ["weekly_cycle_id", "member_id"]
    )


def downgrade() -> None:
    op.drop_table("assignments")
    op.drop_table("weekly_cycles")
