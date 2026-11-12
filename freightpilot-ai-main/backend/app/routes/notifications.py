"""User notification inbox."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.core.security import get_optional_current_user
from app.db.models import Notification, User
from app.db.session import get_db

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


class NotificationResponse(BaseModel):
    id: str
    shipment_id: str | None
    kind: str
    title: str
    message: str
    read_at: datetime | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


def _scope(query, user: User | None):
    return query.filter(Notification.user_id == (user.id if user else None))


@router.get("", response_model=list[NotificationResponse])
def list_notifications(
    unread_only: bool = False, limit: int = 50,
    db: Session = Depends(get_db), user: User | None = Depends(get_optional_current_user),
):
    limit = max(1, min(limit, 100))
    query = _scope(db.query(Notification), user)
    if unread_only:
        query = query.filter(Notification.read_at.is_(None))
    return query.order_by(Notification.created_at.desc()).limit(limit).all()


@router.post("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: str, db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_current_user),
):
    notification = _scope(db.query(Notification), user).filter(Notification.id == notification_id).first()
    if notification is None:
        raise HTTPException(status_code=404, detail={"code": "NOTIFICATION_NOT_FOUND", "message": "Notification not found."})
    if notification.read_at is None:
        notification.read_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(notification)
    return notification
