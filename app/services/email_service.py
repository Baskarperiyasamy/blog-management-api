"""
services/email_service.py — the ONLY module that knows how to send an email
over SMTP. Everything else just calls send_email(to, subject, body).

* Works with Mailtrap (587/2525 STARTTLS) and Gmail (587 STARTTLS or 465 SSL).
* Called through FastAPI BackgroundTasks, so it runs AFTER the API response
  has been returned — a slow/broken mail server never blocks or fails the
  like/comment request.
* send_email() never raises: failures are logged and False is returned.
"""
import logging
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr

from ..config import settings

logger = logging.getLogger("blog_api.email")


def _build_message(to_email: str, subject: str, body: str) -> EmailMessage:
    sender_address = settings.EMAIL_FROM or settings.SMTP_USERNAME
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = formataddr((settings.EMAIL_FROM_NAME, sender_address))
    msg["To"] = to_email
    msg.set_content(body)  # UTF-8 safe plain text
    return msg


def send_email_strict(to_email: str, subject: str, body: str) -> None:
    """Sends the email and RAISES on any problem (used by the test endpoint
    so you can see the real error). Normal code should use send_email()."""
    if not settings.smtp_configured:
        raise RuntimeError(
            "SMTP is not configured. Fill SMTP_HOST, SMTP_USERNAME and "
            "SMTP_PASSWORD in your .env file and restart the server."
        )

    msg = _build_message(to_email, subject, body)
    context = ssl.create_default_context()

    if settings.SMTP_USE_SSL:
        server = smtplib.SMTP_SSL(
            settings.SMTP_HOST, settings.SMTP_PORT,
            timeout=settings.SMTP_TIMEOUT, context=context,
        )
    else:
        server = smtplib.SMTP(
            settings.SMTP_HOST, settings.SMTP_PORT, timeout=settings.SMTP_TIMEOUT
        )

    with server:
        server.ehlo()
        if not settings.SMTP_USE_SSL and settings.SMTP_USE_TLS:
            server.starttls(context=context)
            server.ehlo()
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.send_message(msg)


def send_email(to_email: str, subject: str, body: str) -> bool:
    """Background-safe sender. Returns True on success, False on failure."""
    if not settings.smtp_configured:
        logger.warning(
            "SMTP not configured (.env missing or incomplete) — email NOT sent. "
            "Printing it here instead."
        )
        logger.info("To: %s | Subject: %s\n%s", to_email, subject, body)
        return False

    try:
        send_email_strict(to_email, subject, body)
        logger.info("✅ Email sent to %s (subject: %s)", to_email, subject)
        return True
    except smtplib.SMTPAuthenticationError as e:
        logger.error(
            "❌ SMTP login failed (%s). Check SMTP_USERNAME / SMTP_PASSWORD "
            "(Gmail needs an App Password, not your normal password).", e
        )
    except Exception as e:  # noqa: BLE001 — must never crash the background task
        logger.error("❌ Failed to send email to %s: %s: %s", to_email, type(e).__name__, e)
    return False
