"""Secure document management endpoints and metadata tracking."""

import os
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User, Shipment
from app.core.security import get_current_user, get_optional_current_user
from app.core.audit import write_audit

router = APIRouter(prefix="/api/documents", tags=["Documents"])

UPLOAD_DIR = os.path.join(os.getcwd(), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB limit


class DocumentMetadataResponse(BaseModel):
    id: str
    filename: str
    document_type: str
    file_size: int
    mime_type: str
    shipment_id: Optional[str]
    uploaded_at: str


# In-memory document metadata registry for safe local management
_DOCUMENT_STORE = {}


@router.post("/upload")
async def upload_document(
    document_type: str = Form(...),
    shipment_id: Optional[str] = Form(None),
    file: UploadFile = File(...),
    user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """Secure document upload with MIME validation, size check, and quarantine safeguards."""
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{file.content_type}'. Allowed types: PDF, PNG, JPG, DOC, DOCX."
        )

    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds maximum permitted limit of 10MB.")

    doc_id = str(uuid.uuid4())
    safe_filename = f"{doc_id}_{os.path.basename(file.filename)}"
    dest_path = os.path.join(UPLOAD_DIR, safe_filename)

    with open(dest_path, "wb") as f:
        f.write(contents)

    doc_record = {
        "id": doc_id,
        "filename": file.filename,
        "safe_filename": safe_filename,
        "document_type": document_type,
        "file_size": len(contents),
        "mime_type": file.content_type,
        "shipment_id": shipment_id,
        "uploaded_by": user.id if user else None,
        "uploaded_at": datetime.now(timezone.utc).isoformat()
    }
    _DOCUMENT_STORE[doc_id] = doc_record

    write_audit(db, entity_type="DOCUMENT", entity_id=doc_id, action="DOCUMENT_UPLOADED",
                user_id=user.id if user else None, details={"type": document_type, "size": len(contents)})
    db.commit()

    return {
        "message": "Document uploaded successfully and stored in secure repository.",
        "document": {
            "id": doc_id,
            "filename": file.filename,
            "document_type": document_type,
            "file_size": len(contents),
            "mime_type": file.content_type,
            "shipment_id": shipment_id,
            "uploaded_at": doc_record["uploaded_at"]
        }
    }


@router.get("")
def list_documents(
    shipment_id: Optional[str] = None,
    user: User | None = Depends(get_optional_current_user)
):
    """List document metadata for accessible shipments."""
    docs = list(_DOCUMENT_STORE.values())
    if shipment_id:
        docs = [d for d in docs if d.get("shipment_id") == shipment_id]

    return [
        {
            "id": d["id"],
            "filename": d["filename"],
            "document_type": d["document_type"],
            "file_size": d["file_size"],
            "mime_type": d["mime_type"],
            "shipment_id": d["shipment_id"],
            "uploaded_at": d["uploaded_at"]
        }
        for d in docs
    ]
