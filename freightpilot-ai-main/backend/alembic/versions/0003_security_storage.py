"""Store only verification token hashes and persist private document metadata."""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0003_security_storage"
down_revision: Union[str, None] = "0002_add_role_separation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # The old plaintext token is intentionally removed. Existing outstanding
    # verification links are invalidated and users must request a new link.
    op.drop_column("email_verifications", "token")
    op.create_table(
        "stored_documents",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("owner_id", sa.String(length=36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("shipment_id", sa.String(length=36), sa.ForeignKey("shipments.id", ondelete="CASCADE"), nullable=True),
        sa.Column("storage_key", sa.String(length=100), nullable=False, unique=True),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("document_type", sa.String(length=60), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("scan_status", sa.String(length=30), nullable=False, server_default="NOT_SCANNED"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_stored_documents_owner_id", "stored_documents", ["owner_id"])
    op.create_index("ix_stored_documents_shipment_id", "stored_documents", ["shipment_id"])
    op.create_index("ix_documents_owner_created", "stored_documents", ["owner_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_documents_owner_created", table_name="stored_documents")
    op.drop_index("ix_stored_documents_shipment_id", table_name="stored_documents")
    op.drop_index("ix_stored_documents_owner_id", table_name="stored_documents")
    op.drop_table("stored_documents")
    # Do not re-create a plaintext token column on downgrade.
