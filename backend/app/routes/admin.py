"""Restricted audit log access for administrative review."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.models import AuditLog, User
from app.db.session import get_db

router = APIRouter(prefix="/api/admin", tags=["Administration"])


@router.get("/audit-logs")
def list_audit_logs(
    entity_type: str | None = None, entity_id: str | None = None, limit: int = 100,
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    if user.role != "ADMIN":
        raise HTTPException(status_code=403, detail={"code": "ADMIN_REQUIRED", "message": "Administrator access is required."})
    query = db.query(AuditLog)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type.upper())
    if entity_id:
        query = query.filter(AuditLog.entity_id == entity_id)
    rows = query.order_by(AuditLog.created_at.desc()).limit(max(1, min(limit, 500))).all()
    return [{"id": row.id, "user_id": row.user_id, "entity_type": row.entity_type,
             "entity_id": row.entity_id, "action": row.action, "details": row.details,
             "created_at": row.created_at.isoformat()} for row in rows]
