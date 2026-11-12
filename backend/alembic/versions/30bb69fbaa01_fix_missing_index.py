"""Fix duplicate index on payments.provider_capture_id.

The initial migration created both a unique constraint and an explicit index
on provider_capture_id. The unique constraint implicitly creates an index,
so the explicit index is a duplicate. This migration removes the duplicate
explicit index while preserving the unique constraint.

Revision ID: 30bb69fbaa01
Revises: 0005_add_user_delete_columns
Create Date: 2026-11-12 22:32:13.438737

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision: str = '30bb69fbaa01'
down_revision: Union[str, None] = '0005_add_user_delete_columns'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _index_exists(connection, table_name: str, index_name: str) -> bool:
    """Check if an index exists on a table."""
    inspector = inspect(connection)
    indexes = inspector.get_indexes(table_name)
    return any(idx['name'] == index_name for idx in indexes)


def _constraint_exists(connection, table_name: str, constraint_name: str) -> bool:
    """Check if a unique constraint exists on a table."""
    inspector = inspect(connection)
    constraints = inspector.get_unique_constraints(table_name)
    return any(c['name'] == constraint_name for c in constraints)


def upgrade() -> None:
    # The initial migration created both a unique constraint and an explicit index
    # on payments.provider_capture_id. The unique constraint implicitly creates
    # a unique index, so the explicit index (ix_payments_provider_capture_id)
    # is a duplicate. We remove the duplicate explicit index.

    # The unique constraint name is uq_payments_provider_capture_id
    # The explicit index name is ix_payments_provider_capture_id
    # We want to drop the explicit index, NOT the unique constraint.

    connection = op.get_bind()

    # Drop the duplicate explicit index if it exists
    # Use raw SQL for PostgreSQL compatibility with IF EXISTS
    if _index_exists(connection, 'payments', 'ix_payments_provider_capture_id'):
        op.execute('DROP INDEX IF EXISTS ix_payments_provider_capture_id')


def downgrade() -> None:
    # Recreate the explicit index (the duplicate that was removed)
    # This is a non-unique index in the downgrade since the unique constraint
    # already provides the uniqueness guarantee.
    connection = op.get_bind()

    if not _index_exists(connection, 'payments', 'ix_payments_provider_capture_id'):
        op.create_index(
            'ix_payments_provider_capture_id',
            'payments',
            ['provider_capture_id'],
            unique=False
        )