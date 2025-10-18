"""Add STOPPED to taskstatus enum

Revision ID: 2025_add_stopped_taskstatus
Revises: 5e55a9be3e58
Create Date: 2025-10-18 00:00:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2025_add_stopped_taskstatus"
down_revision: Union[str, None] = "5e55a9be3e58"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create the new enum type with the additional value
    op.execute(
        "CREATE TYPE taskstatus_new AS ENUM('PENDING','PROCESSING','COMPLETED','FAILED','STOPPED')"
    )
    # Alter the column to use the new type
    op.execute(
        "ALTER TABLE usertask ALTER COLUMN status TYPE taskstatus_new USING status::text::taskstatus_new"
    )
    # Drop the old type and rename the new one
    op.execute("DROP TYPE taskstatus")
    op.execute("ALTER TYPE taskstatus_new RENAME TO taskstatus")


def downgrade() -> None:
    # Recreate the old enum without STOPPED
    op.execute(
        "CREATE TYPE taskstatus_old AS ENUM('PENDING','PROCESSING','COMPLETED','FAILED')"
    )
    op.execute(
        "ALTER TABLE usertask ALTER COLUMN status TYPE taskstatus_old USING status::text::taskstatus_old"
    )
    op.execute("DROP TYPE taskstatus")
    op.execute("ALTER TYPE taskstatus_old RENAME TO taskstatus")
