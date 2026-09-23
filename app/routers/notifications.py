"""
<<<<<<< HEAD
routers/notifications.py — two things live here:

  1. SMTP test/status helpers (unchanged, below) for checking your email
     setup without creating posts/comments first.
  2. The in-app Notification Center (bell icon) API: list notifications,
     get the unread count, and mark one or all as read.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import models, schemas
from ..config import settings
from ..database import get_db
=======
routers/notifications.py — a small helper endpoint to TEST your SMTP setup
without having to create posts/comments first.
"""
from fastapi import APIRouter, Depends, HTTPException

from .. import models
from ..config import settings
>>>>>>> 403a1134133178c9857fb7d9cd5b11da2db05a74
from ..deps import get_current_user
from ..services.email_service import send_email_strict
from ..services.notification_service import build_comment_notification

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/status")
def smtp_status():
    """Shows which SMTP settings the app actually loaded (password hidden)."""
    return {
        "smtp_configured": settings.smtp_configured,
        "host": settings.SMTP_HOST,
        "port": settings.SMTP_PORT,
        "username": settings.SMTP_USERNAME,
        "password_set": bool(settings.SMTP_PASSWORD),
        "use_tls_starttls": settings.SMTP_USE_TLS and not settings.SMTP_USE_SSL,
        "use_ssl": settings.SMTP_USE_SSL,
        "email_from": settings.EMAIL_FROM or settings.SMTP_USERNAME,
        "timezone": settings.TIMEZONE,
    }


@router.post("/test-email")
def send_test_email(current_user: models.User = Depends(get_current_user)):
    """Sends a sample notification email to YOUR registered email address and
    returns the exact SMTP error if it fails."""
    subject, body = build_comment_notification("Test Post — SMTP check", "Test User")
    try:
        send_email_strict(current_user.email, subject, body)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"{type(e).__name__}: {e}")
    return {"sent": True, "to": current_user.email}
<<<<<<< HEAD


# ---------------------------------------------------------------------------
# In-app Notification Center (bell icon)
# ---------------------------------------------------------------------------
@router.get("", response_model=schemas.NotificationListOut)
def list_notifications(
    limit: int = Query(20, ge=1, le=100),
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Lists the authenticated user's own notifications, most recent first,
    plus their current unread count (for the bell icon's badge). A user
    can only ever see their own notifications - identity comes from the
    JWT, there is no user_id parameter.
    """
    query = db.query(models.Notification).filter(models.Notification.user_id == current_user.id)
    if unread_only:
        query = query.filter(models.Notification.is_read.is_(False))

    notifications = query.order_by(models.Notification.created_at.desc()).limit(limit).all()

    unread_count = (
        db.query(models.Notification)
        .filter(models.Notification.user_id == current_user.id, models.Notification.is_read.is_(False))
        .count()
    )

    return schemas.NotificationListOut(
        unread_count=unread_count,
        notifications=[schemas.NotificationOut.model_validate(n) for n in notifications],
    )


@router.get("/unread-count")
def unread_count(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Just the badge number - lightweight endpoint to poll frequently."""
    count = (
        db.query(models.Notification)
        .filter(models.Notification.user_id == current_user.id, models.Notification.is_read.is_(False))
        .count()
    )
    return {"unread_count": count}


@router.post("/{notification_id}/read", response_model=schemas.MarkReadOut)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Marks a single notification as read. 404s if it isn't yours."""
    notification = (
        db.query(models.Notification)
        .filter(models.Notification.id == notification_id, models.Notification.user_id == current_user.id)
        .first()
    )
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.is_read = True
    db.commit()
    return schemas.MarkReadOut(id=notification.id, is_read=True)


@router.post("/read-all", response_model=schemas.MarkAllReadOut)
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Marks every unread notification belonging to the caller as read."""
    updated = (
        db.query(models.Notification)
        .filter(models.Notification.user_id == current_user.id, models.Notification.is_read.is_(False))
        .update({"is_read": True})
    )
    db.commit()
    return schemas.MarkAllReadOut(marked_read=updated)
=======
>>>>>>> 403a1134133178c9857fb7d9cd5b11da2db05a74
