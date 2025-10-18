"""Add task_id column to usertask

Revision ID: 2025_add_usertask_task_id
Revises: 2025_add_stopped_taskstatus
Create Date: 2025-10-18 00:10:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2025_add_usertask_task_id"
down_revision: Union[str, None] = "2025_add_stopped_taskstatus"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add task_id column to store Celery broker task ids
    op.add_column("usertask", sa.Column("task_id", sa.Text(), nullable=True))
    op.create_index(op.f("ix_usertask_task_id"), "usertask", ["task_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_usertask_task_id"), table_name="usertask")
    op.drop_column("usertask", "task_id")
