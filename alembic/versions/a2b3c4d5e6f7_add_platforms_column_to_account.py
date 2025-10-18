"""add_platforms_column_to_account

Revision ID: a2b3c4d5e6f7
Revises: 9a1b2c3d4e5f
Create Date: 2025-10-18 00:30:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a2b3c4d5e6f7"
down_revision: Union[str, None] = "9a1b2c3d4e5f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = [c["name"] for c in inspector.get_columns("account")]
    if "platforms" not in cols:
        op.add_column(
            "account", sa.Column("platforms", sa.String(length=255), nullable=True)
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = [c["name"] for c in inspector.get_columns("account")]
    if "platforms" in cols:
        op.drop_column("account", "platforms")
