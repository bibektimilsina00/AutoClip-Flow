"""task foregin key fixed

Revision ID: ec3f7bb80b74
Revises: 0c7bc5fcebcb
Create Date: 2024-11-03 21:30:23.432346

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ec3f7bb80b74'
down_revision: Union[str, None] = '0c7bc5fcebcb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###