"""rename_platforms_to_platform

Revision ID: 8254128f3d56
Revises: 4a233d112f35
Create Date: 2025-10-17 23:43:23.279113

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "8254128f3d56"
down_revision: Union[str, None] = "4a233d112f35"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename the existing 'platforms' column to 'platform' on the 'account' table.
    # Use a safe approach that works across multiple DB backends by adding the
    # new column, copying values, then dropping the old column and renaming as
    # necessary. For PostgreSQL we can use simple ALTER TABLE RENAME if desired,
    # but using SQL here keeps it explicit.
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = [c["name"] for c in inspector.get_columns("account")]
    if "platforms" in cols and "platform" not in cols:
        # Add the new column with the same type as the old one (varchar/STRING).
        op.add_column(
            "account",
            sa.Column(
                "platform",
                sa.String(length=255),
                nullable=False,
                server_default="TIKTOK",
            ),
        )
        # Copy values from old column to new column
        op.execute("UPDATE account SET platform = platforms")
        # Drop the old column
        op.drop_column("account", "platforms")
        # Remove server default if not desired
        op.alter_column("account", "platform", server_default=None)


def downgrade() -> None:
    # Reverse the rename: recreate 'platforms' column and copy values back.
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = [c["name"] for c in inspector.get_columns("account")]
    if "platform" in cols and "platforms" not in cols:
        op.add_column(
            "account",
            sa.Column(
                "platforms",
                sa.String(length=255),
                nullable=False,
                server_default="TIKTOK",
            ),
        )
        op.execute("UPDATE account SET platforms = platform")
        op.drop_column("account", "platform")
        op.alter_column("account", "platforms", server_default=None)
