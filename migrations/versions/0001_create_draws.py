"""create draws table

Revision ID: 0001
Revises:
Create Date: 2026-08-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "draws",
        sa.Column("draw_no", sa.SmallInteger(), primary_key=True),
        sa.Column("n1", sa.SmallInteger(), nullable=False),
        sa.Column("n2", sa.SmallInteger(), nullable=False),
        sa.Column("n3", sa.SmallInteger(), nullable=False),
        sa.Column("n4", sa.SmallInteger(), nullable=False),
        sa.Column("n5", sa.SmallInteger(), nullable=False),
        sa.Column("n6", sa.SmallInteger(), nullable=False),
        sa.Column("bonus_no", sa.SmallInteger(), nullable=False),
        sa.Column("draw_date", sa.Date(), nullable=False),
        sa.Column("source", sa.String(length=20), nullable=False),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_table("draws")
