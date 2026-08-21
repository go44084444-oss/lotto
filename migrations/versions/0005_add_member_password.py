"""add hashed_password to members

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: Union[str, Sequence[str], None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "members", sa.Column("hashed_password", sa.String(length=255), nullable=False)
    )


def downgrade() -> None:
    op.drop_column("members", "hashed_password")
