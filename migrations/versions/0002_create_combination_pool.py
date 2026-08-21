"""create combination_pool table

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, Sequence[str], None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "combination_pool",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=False),
        sa.Column("numbers", sa.ARRAY(sa.SmallInteger()), nullable=False),
        sa.Column("combo_key", sa.BigInteger(), nullable=False),
    )
    op.create_unique_constraint(
        "uq_combination_pool_combo_key", "combination_pool", ["combo_key"]
    )


def downgrade() -> None:
    op.drop_table("combination_pool")
