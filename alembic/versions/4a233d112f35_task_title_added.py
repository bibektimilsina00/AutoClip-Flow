"""task title added

Revision ID: 4a233d112f35
Revises: 9c371e9699bf
Create Date: 2024-11-04 12:26:13.029691

"""

from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4a233d112f35"
down_revision: Union[str, None] = "9c371e9699bf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "usertask",
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("usertask", "title")
    # ### end Alembic commands ###