"""empty message

Revision ID: 93043cc376fd
Revises: f7d156579dc2
Create Date: 2024-10-24 12:15:36.549801

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '93043cc376fd'
down_revision: Union[str, None] = 'f7d156579dc2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('leroymerlin_items', 'page')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('leroymerlin_items', sa.Column('page', sa.INTEGER(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
