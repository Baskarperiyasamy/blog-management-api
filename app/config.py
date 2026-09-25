"""
config.py — all settings are read from the .env file (or real environment
variables). Copy .env.example to .env and fill in your SMTP credentials.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

# Always load the .env that sits next to the "app" folder (blog_api/.env),
# no matter which directory you start uvicorn from.
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def _get_str(name: str, default: str = "") -> str:
    # strip() removes accidental spaces / quotes copied from a website.
    return os.getenv(name, default).strip().strip('"').strip("'")


class Settings:
    SECRET_KEY = _get_str("SECRET_KEY", "CHANGE_THIS_SECRET_KEY_IN_PRODUCTION")

    # --- Email (SMTP) ---
    SMTP_HOST = _get_str("SMTP_HOST")
    SMTP_PORT = int(_get_str("SMTP_PORT", "587") or "587")
    SMTP_USERNAME = _get_str("SMTP_USERNAME")
    # Gmail shows App Passwords as "abcd efgh ijkl mnop" — the spaces must go.
    SMTP_PASSWORD = _get_str("SMTP_PASSWORD").replace(" ", "")
    EMAIL_FROM = _get_str("EMAIL_FROM")
    EMAIL_FROM_NAME = _get_str("EMAIL_FROM_NAME", "Blog Management API")

    # Connection security:
    #   port 587 / 2525 / 25  -> STARTTLS  (SMTP_USE_TLS=true,  SMTP_USE_SSL=false)
    #   port 465              -> SSL       (SMTP_USE_SSL=true)
    # If left blank they are chosen automatically from the port.
    SMTP_USE_SSL = _get_bool("SMTP_USE_SSL", SMTP_PORT == 465)
    SMTP_USE_TLS = _get_bool("SMTP_USE_TLS", SMTP_PORT != 465)
    SMTP_TIMEOUT = int(_get_str("SMTP_TIMEOUT", "15") or "15")

    # Timezone used for the "Time:" line in the email.
    TIMEZONE = _get_str("TIMEZONE", "Asia/Kolkata")

    # By default you are NOT emailed about your own likes/comments.
    # Set to true only if you want to test with a single account.
    NOTIFY_ON_OWN_ACTIVITY = _get_bool("NOTIFY_ON_OWN_ACTIVITY", False)

    # --- AI Support Chat ---
    # Optional. If left blank, the chat endpoint automatically falls back to
    # the built-in FAQ responses (see services/ai_support_service.py) -
    # no key is required to use this feature.
    OPENAI_API_KEY = _get_str("OPENAI_API_KEY")
    OPENAI_MODEL = _get_str("OPENAI_MODEL", "gpt-4o-mini")

    @property
    def openai_configured(self) -> bool:
        return bool(self.OPENAI_API_KEY)

    # --- Auth0 (Google / Facebook social login) ---
    # Leave AUTH0_DOMAIN blank and the social login buttons will show a
    # clear "not configured" error instead of crashing - normal email/
    # password signup and login keep working either way.
    AUTH0_DOMAIN = _get_str("AUTH0_DOMAIN")                 # e.g. dev-xxxxxxx.us.auth0.com
    AUTH0_CLIENT_ID = _get_str("AUTH0_CLIENT_ID")
    AUTH0_CLIENT_SECRET = _get_str("AUTH0_CLIENT_SECRET")
    AUTH0_CALLBACK_URL = _get_str("AUTH0_CALLBACK_URL", "http://127.0.0.1:8000/auth/callback")
    # Where to send the browser after a successful social login, with the
    # app's own JWT attached as a #token= fragment for the page to read.
    FRONTEND_LOGIN_REDIRECT = _get_str("FRONTEND_LOGIN_REDIRECT", "http://127.0.0.1:8000/static/login.html")

    @property
    def auth0_configured(self) -> bool:
        return bool(self.AUTH0_DOMAIN and self.AUTH0_CLIENT_ID and self.AUTH0_CLIENT_SECRET)

    @property
    def smtp_configured(self) -> bool:
        return bool(self.SMTP_HOST and self.SMTP_USERNAME and self.SMTP_PASSWORD)


settings = Settings()
