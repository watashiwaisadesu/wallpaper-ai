"""empty message

Revision ID: faf323784b03
Revises: c8c10e570ba3
Create Date: 2024-10-21 17:33:18.788845

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'faf323784b03'
down_revision: Union[str, None] = 'c8c10e570ba3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('wallpapers',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('url', sa.String(), nullable=True),
    sa.Column('image_url', sa.String(), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('price', sa.Float(), nullable=True),
    sa.Column('item_name', sa.String(), nullable=True),
    sa.Column('page_number', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_wallpapers_id'), 'wallpapers', ['id'], unique=False)
    op.create_index(op.f('ix_wallpapers_url'), 'wallpapers', ['url'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_wallpapers_url'), table_name='wallpapers')
    op.drop_index(op.f('ix_wallpapers_id'), table_name='wallpapers')
    op.drop_table('wallpapers')
    # ### end Alembic commands ###
