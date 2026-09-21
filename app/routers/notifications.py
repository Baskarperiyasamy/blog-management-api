"""
routers/notifications.py — a small helper endpoint to TEST your SMTP setup
without having to create posts/comments first.
"""
from fastapi import APIRouter, Depends, HTTPException

from .. import models
from ..config import settings
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
