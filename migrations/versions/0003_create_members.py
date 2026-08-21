"""create membership_tiers and members tables

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0003"
down_revision: Union[str, Sequence[str], None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    membership_tiers = op.create_table(
        "membership_tiers",
        sa.Column("code", sa.String(length=20), primary_key=True),
        sa.Column("weekly_quota", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(length=50), nullable=False),
    )
    op.bulk_insert(
        membership_tiers,
        [{"code": "free", "weekly_quota": 20, "display_name": "무료 회원"}],
    )

    op.create_table(
        "members",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("tier", sa.String(length=20), nullable=False, server_default="free"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("withdrawn_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["tier"], ["membership_tiers.code"]),
        sa.CheckConstraint("status IN ('active', 'withdrawn')", name="ck_members_status"),
    )


def downgrade() -> None:
    op.drop_table("members")
    op.drop_table("membership_tiers")
