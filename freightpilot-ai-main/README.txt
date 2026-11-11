PostgreSQL document storage patch

Contains four replacement files. Extract at the project root so the backend/ folder merges into your existing backend/.

IMPORTANT: Back up your existing files first. Apply the Alembic migration to add stored_documents.content BYTEA before deploying. Existing external files are not migrated automatically. Documents without a CLEAN scan status remain unavailable for download.
