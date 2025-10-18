"""add_facebook_fields_to_account

Revision ID: 9a1b2c3d4e5f
Revises: 8254128f3d56
Create Date: 2025-10-17 23:59:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9a1b2c3d4e5f"
down_revision: Union[str, None] = "8254128f3d56"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = [c["name"] for c in inspector.get_columns("account")]
    if "facebook_page_id" not in cols:
        op.add_column(
            "account",
            sa.Column("facebook_page_id", sa.String(length=255), nullable=True),
        )
    if "facebook_group_id" not in cols:
        op.add_column(
            "account",
            sa.Column("facebook_group_id", sa.String(length=255), nullable=True),
        )
    if "facebook_post_to_page" not in cols:
        op.add_column(
            "account",
            sa.Column(
                "facebook_post_to_page",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
        )
    if "facebook_post_to_group" not in cols:
        op.add_column(
            "account",
            sa.Column(
                "facebook_post_to_group",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    cols = [c["name"] for c in inspector.get_columns("account")]
    if "facebook_page_id" in cols:
        op.drop_column("account", "facebook_page_id")
    if "facebook_group_id" in cols:
        op.drop_column("account", "facebook_group_id")
    if "facebook_post_to_page" in cols:
        op.drop_column("account", "facebook_post_to_page")
    if "facebook_post_to_group" in cols:
        op.drop_column("account", "facebook_post_to_group")
