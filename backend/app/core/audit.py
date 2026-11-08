"""Small helpers for durable audit and notification records."""

from app.db.models import AuditLog, Notification


def write_audit(db, *, entity_type: str, entity_id: str, action: str,
                user_id: str | None = None, details: dict | None = None) -> None:
    db.add(AuditLog(
        user_id=user_id, entity_type=entity_type, entity_id=entity_id,
        action=action, details=details or {},
    ))


def create_notification(db, *, title: str, message: str, kind: str,
                        user_id: str | None = None, shipment_id: str | None = None) -> None:
    db.add(Notification(
        user_id=user_id, shipment_id=shipment_id, kind=kind,
        title=title, message=message,
    ))
