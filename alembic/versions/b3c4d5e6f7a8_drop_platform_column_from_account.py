"""drop_platform_column_from_account

Revision ID: b3c4d5e6f7a8
Revises: a2b3c4d5e6f7
Create Date: 2025-10-18 00:45:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b3c4d5e6f7a8"
down_revision: Union[str, None] = "a2b3c4d5e6f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = [c["name"] for c in inspector.get_columns("account")]
    if "platform" in cols:
        op.drop_column("account", "platform")


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = [c["name"] for c in inspector.get_columns("account")]
    if "platform" not in cols:
        # Recreate as nullable string to be safe; enum restoration not attempted here.
        op.add_column(
            "account", sa.Column("platform", sa.String(length=255), nullable=True)
        )
