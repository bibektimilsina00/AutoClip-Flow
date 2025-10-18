"""merge heads for google key fields

Revision ID: merge_add_google_key_heads
Revises: add_google_key_fields_to_user, b3c4d5e6f7a8
Create Date: 2025-10-18 19:25:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "merge_add_google_key_heads"
down_revision = ("add_google_key_fields_to_user", "b3c4d5e6f7a8")
branch_labels = None
depends_on = None


def upgrade():
    # merge-only revision; no DB changes
    pass


def downgrade():
    pass
