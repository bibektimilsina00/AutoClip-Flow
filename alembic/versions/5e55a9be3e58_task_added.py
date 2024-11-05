"""task added 

Revision ID: 5e55a9be3e58
Revises: c3da6d967230
Create Date: 2024-11-02 17:47:39.831116

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '5e55a9be3e58'
down_revision: Union[str, None] = 'c3da6d967230'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('usertask',
    sa.Column('task_id', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('status', sa.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', name='taskstatus'), nullable=False),
    sa.Column('progress', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('account_id', sa.Uuid(), nullable=True),
    sa.ForeignKeyConstraint(['account_id'], ['account.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_usertask_task_id'), 'usertask', ['task_id'], unique=True)
    op.create_index(op.f('ix_usertask_user_id'), 'usertask', ['user_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_usertask_user_id'), table_name='usertask')
    op.drop_index(op.f('ix_usertask_task_id'), table_name='usertask')
    op.drop_table('usertask')
    # ### end Alembic commands ###
