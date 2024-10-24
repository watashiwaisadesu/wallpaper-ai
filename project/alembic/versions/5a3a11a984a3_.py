"""empty message

Revision ID: 5a3a11a984a3
Revises: ef1d3edf83be
Create Date: 2024-10-23 23:52:45.415597

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5a3a11a984a3'
down_revision: Union[str, None] = 'ef1d3edf83be'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    # Step 1: Drop the existing table if it exists
    op.drop_table('leroymerlin_items')

    # Step 2: Create a new table with the desired structure
    op.create_table(
        'leroymerlin_items',
        sa.Column('id', sa.UUID(), nullable=False, primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('image_url', sa.String(), nullable=True),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('price_type', sa.String(), nullable=True),
        sa.Column('product_type', sa.String(), nullable=False)
    )

def downgrade() -> None:
    # Step 1: Drop the newly created table
    op.drop_table('leroymerlin_items')

    # Step 2: Recreate the original table structure
    op.create_table(
        'leroymerlin_items',
        sa.Column('id', sa.INTEGER(), nullable=False, primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('image_url', sa.String(), nullable=True),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('price_type', sa.String(), nullable=True),
        sa.Column('product_type', sa.String(), nullable=False)
    )
