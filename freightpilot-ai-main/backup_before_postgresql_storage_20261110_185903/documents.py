"""Private document storage with ownership checks, streamed size limits and file-signature validation."""
import hashlib
import os
import socket
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse, StreamingResponse
from urllib.parse import quote
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.core.access import get_accessible_shipment
from app.core.audit import write_audit
from app.core.security import get_current_user
from app.db.models import StoredDocument, User
from app.db.session import get_db
from app.services import document_storage

router = APIRouter(prefix="/api/documents", tags=["Documents"])
_ALLOWED_SIGNATURES = {
    ".pdf": ("application/pdf", lambda b: b.startswith(b"%PDF-")),
    ".png": ("image/png", lambda b: b.startswith(b"\x89PNG\r\n\x1a\n")),
    ".jpg": ("image/jpeg", lambda b: b.startswith(b"\xff\xd8\xff")),
    ".jpeg": ("image/jpeg", lambda b: b.startswith(b"\xff\xd8\xff")),
}
_CHUNK_SIZE = 1024 * 1024


class DocumentMetadataResponse(BaseModel):
    id: str
    filename: str
    document_type: str
    file_size: int
    mime_type: str
    shipment_id: Optional[str]
    uploaded_at: str
    scan_status: str


def _file_path(storage_key: str) -> Path:
    root = Path(settings.DOCUMENT_STORAGE_PATH).resolve()
    target = (root / storage_key).resolve()
    if root not in target.parents:
        raise HTTPException(status_code=400, detail={"code": "INVALID_STORAGE_KEY", "message": "Invalid document key."})
    return target


def _clamav_scan(path: Path) -> str:
    """Scan a saved file through ClamAV's INSTREAM TCP protocol."""
    if not settings.CLAMAV_HOST:
        return "PENDING_SCAN"
    try:
        with socket.create_connection((settings.CLAMAV_HOST, settings.CLAMAV_PORT), timeout=8) as sock:
            sock.settimeout(20)
            sock.sendall(b"zINSTREAM\0")
            with path.open("rb") as source:
                while chunk := source.read(64 * 1024):
                    sock.sendall(len(chunk).to_bytes(4, "big"))
                    sock.sendall(chunk)
            sock.sendall((0).to_bytes(4, "big"))
            response = sock.recv(4096).decode("utf-8", errors="replace")
        if response.strip().endswith("OK"):
            return "CLEAN"
        if "FOUND" in response:
            return "INFECTED"
        raise RuntimeError("ClamAV returned an unrecognized result")
    except Exception as exc:
        raise RuntimeError("Malware scanner is unavailable; document remains quarantined.") from exc


def _can_access(document: StoredDocument, user: User) -> bool:
    return user.role == "ADMIN" or document.owner_id == user.id


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    document_type: str = Form(..., min_length=2, max_length=60),
    shipment_id: Optional[str] = Form(None),
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if shipment_id:
        shipment = None if user.role == "ADMIN" else get_accessible_shipment(db, shipment_id, user)
        if user.role not in {"BUYER", "ADMIN"}:
            raise HTTPException(status_code=403, detail={"code": "DOCUMENT_UPLOAD_FORBIDDEN", "message": "Only the shipment owner or an administrator can upload shipment documents."})
        if user.role != "ADMIN" and shipment.user_id != user.id:
            raise HTTPException(status_code=404, detail={"code": "SHIPMENT_NOT_FOUND", "message": "Shipment not found."})

    filename = Path(file.filename or "document").name
    if not filename or len(filename) > 255:
        raise HTTPException(status_code=422, detail={"code": "INVALID_FILENAME", "message": "Filename is invalid."})
    extension = Path(filename).suffix.lower()
    signature = _ALLOWED_SIGNATURES.get(extension)
    if signature is None:
        raise HTTPException(status_code=415, detail={"code": "FILE_TYPE_NOT_ALLOWED", "message": "Only PDF, PNG and JPEG files are accepted."})

    storage_key = f"{uuid.uuid4().hex}{extension}"
    target = _file_path(storage_key)
    target.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    total = 0
    prefix = bytearray()
    stored_remotely = False
    try:
        with target.open("xb") as output:
            while True:
                chunk = await file.read(_CHUNK_SIZE)
                if not chunk:
                    break
                total += len(chunk)
                if total > settings.MAX_UPLOAD_BYTES:
                    raise HTTPException(status_code=413, detail={"code": "FILE_TOO_LARGE", "message": f"File exceeds the {settings.MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit."})
                if len(prefix) < 16:
                    prefix.extend(chunk[:16 - len(prefix)])
                digest.update(chunk)
                output.write(chunk)
        expected_mime, valid_signature = signature
        if not total or not valid_signature(bytes(prefix)):
            raise HTTPException(status_code=415, detail={"code": "FILE_SIGNATURE_INVALID", "message": "The file contents do not match an allowed file type."})
        try:
            scan_status = _clamav_scan(target)
        except RuntimeError as exc:
            scan_status = "PENDING_SCAN"
        if scan_status == "INFECTED":
            raise HTTPException(status_code=422, detail={"code": "MALWARE_DETECTED", "message": "The uploaded file failed malware scanning."})
        # If no scanner is configured, the document remains quarantined and cannot be downloaded.
        if settings.STORAGE_BACKEND == "s3":
            document_storage.store_file(target, storage_key)
            stored_remotely = True
            target.unlink(missing_ok=True)
        document = StoredDocument(
            owner_id=user.id, shipment_id=shipment_id, storage_key=storage_key,
            original_filename=filename, document_type=document_type, mime_type=expected_mime, file_size=total,
            sha256=digest.hexdigest(), scan_status=scan_status,
        )
        db.add(document)
        write_audit(db, entity_type="DOCUMENT", entity_id=document.id, action="DOCUMENT_UPLOADED",
                    user_id=user.id, details={"shipment_id": shipment_id, "mime_type": expected_mime, "file_size": total})
        db.commit()
        db.refresh(document)
    except Exception:
        db.rollback()
        target.unlink(missing_ok=True)
        if stored_remotely:
            try:
                document_storage.delete_file(storage_key)
            except Exception:
                pass
        raise
    finally:
        await file.close()

    return {
        "id": document.id, "filename": document.original_filename,
        "document_type": document_type, "file_size": document.file_size,
        "mime_type": document.mime_type, "shipment_id": document.shipment_id,
        "uploaded_at": document.created_at.isoformat(), "scan_status": document.scan_status,
        "message": "Document stored privately. It is downloadable only after a clean malware scan." if document.scan_status != "CLEAN" else "Document stored privately and passed malware scanning.",
    }


@router.get("")
def list_documents(
    shipment_id: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(StoredDocument)
    if user.role != "ADMIN":
        query = query.filter(StoredDocument.owner_id == user.id)
    if shipment_id:
        query = query.filter(StoredDocument.shipment_id == shipment_id)
    rows = query.order_by(StoredDocument.created_at.desc()).limit(100).all()
    return [{
        "id": d.id, "filename": d.original_filename, "file_size": d.file_size,
        "document_type": d.document_type, "mime_type": d.mime_type, "shipment_id": d.shipment_id,
        "uploaded_at": d.created_at.isoformat(), "scan_status": d.scan_status,
    } for d in rows]


@router.get("/{document_id}/download")
def download_document(
    document_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document = db.query(StoredDocument).filter(StoredDocument.id == document_id).first()
    if document is None or not _can_access(document, user):
        raise HTTPException(status_code=404, detail={"code": "DOCUMENT_NOT_FOUND", "message": "Document not found."})
    if document.scan_status != "CLEAN":
        raise HTTPException(status_code=423, detail={"code": "DOCUMENT_QUARANTINED", "message": "The document is unavailable until malware scanning completes."})
    if not document_storage.file_exists(document.storage_key):
        raise HTTPException(status_code=404, detail={"code": "DOCUMENT_FILE_MISSING", "message": "Stored document is unavailable."})
    headers = {
        "X-Content-Type-Options": "nosniff",
        "Cache-Control": "private, no-store",
        "Content-Disposition": f"attachment; filename*=UTF-8''{quote(document.original_filename)}",
    }
    if settings.STORAGE_BACKEND == "local":
        return FileResponse(_file_path(document.storage_key), media_type=document.mime_type, filename=document.original_filename, headers=headers)
    body = document_storage.open_file(document.storage_key)
    return StreamingResponse(body, media_type=document.mime_type, headers=headers)


@router.delete("/{document_id}", status_code=204)
def delete_document(
    document_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document = db.query(StoredDocument).filter(StoredDocument.id == document_id).first()
    if document is None or not _can_access(document, user):
        raise HTTPException(status_code=404, detail={"code": "DOCUMENT_NOT_FOUND", "message": "Document not found."})
    document_storage.delete_file(document.storage_key)
    write_audit(db, entity_type="DOCUMENT", entity_id=document.id, action="DOCUMENT_DELETED", user_id=user.id)
    db.delete(document)
    db.commit()
    return None
