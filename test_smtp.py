"""
Run this FIRST to check your SMTP settings, before starting the API:

    python test_smtp.py                 # sends to your Mailtrap/Gmail inbox
    python test_smtp.py someone@x.com   # sends to a specific address

It prints the exact reason if something is wrong.
"""
import sys

from app.config import settings
from app.services.email_service import send_email_strict
from app.services.notification_service import build_comment_notification

print("Loaded settings:")
print(f"  SMTP_HOST     = {settings.SMTP_HOST!r}")
print(f"  SMTP_PORT     = {settings.SMTP_PORT}")
print(f"  SMTP_USERNAME = {settings.SMTP_USERNAME!r}")
print(f"  SMTP_PASSWORD = {'(set, %d chars)' % len(settings.SMTP_PASSWORD) if settings.SMTP_PASSWORD else '(EMPTY!)'}")
print(f"  SSL={settings.SMTP_USE_SSL}  STARTTLS={settings.SMTP_USE_TLS}")
print()

to = sys.argv[1] if len(sys.argv) > 1 else (settings.EMAIL_FROM or settings.SMTP_USERNAME)
subject, body = build_comment_notification("SMTP Test Post", "Test User")
try:
    send_email_strict(to, subject, body)
    print(f"✅ SUCCESS — email sent to {to}. Check your inbox.")
except Exception as e:
    print(f"❌ FAILED: {type(e).__name__}: {e}")
    print("\nCommon fixes:")
    print("  * No .env file?  Copy .env.example to .env and fill it in.")
    print("  * Mailtrap: copy username/password from Inboxes > SMTP Settings.")
    print("  * Gmail: use a 16-character App Password (needs 2-Step Verification).")
    sys.exit(1)
