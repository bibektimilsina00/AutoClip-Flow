"""add google key fields to user

Revision ID: add_google_key_fields_to_user
Revises:
Create Date: 2025-10-18 19:20:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "add_google_key_fields_to_user"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "user",
        sa.Column("google_service_account_file", sa.String(length=1024), nullable=True),
    )
    op.add_column(
        "user",
        sa.Column("google_service_account_uploaded_at", sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_column("user", "google_service_account_uploaded_at")
    op.drop_column("user", "google_service_account_file")
