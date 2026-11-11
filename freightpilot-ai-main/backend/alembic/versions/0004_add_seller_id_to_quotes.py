"""add_seller_id_to_quotes

Revision ID: 0004_add_seller_id_to_quotes
Revises: 0003_security_storage
Create Date: 2026-11-09 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0004_add_seller_id_to_quotes'
down_revision: Union[str, None] = '0003_security_storage'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add seller_id column to quotes table
    op.add_column('quotes', sa.Column('seller_id', sa.String(length=36), nullable=True))
    op.create_index(op.f('ix_quotes_seller_id'), 'quotes', ['seller_id'], unique=False)
    op.create_foreign_key('fk_quotes_seller_id_users', 'quotes', 'users', ['seller_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    op.drop_constraint('fk_quotes_seller_id_users', 'quotes', type_='foreignkey')
    op.drop_index(op.f('ix_quotes_seller_id'), table_name='quotes')
    op.drop_column('quotes', 'seller_id')