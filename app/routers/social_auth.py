"""
routers/social_auth.py — the two "Continue with Google / Facebook" buttons.

  GET /auth/login/google    -> redirects the browser to Auth0
  GET /auth/login/facebook  -> redirects the browser to Auth0
  GET /auth/callback        -> Auth0 redirects back here after login;
                                 creates/updates the user, issues our own
                                 JWT, and redirects to the frontend with it.

Kept separate from routers/auth.py (email/password signup+login) so each
file stays focused on one thing.
"""
import logging
import secrets
import time
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from .. import models
from ..config import settings
from ..database import SessionLocal
from ..security import create_access_token
from ..services.auth0_service import build_authorize_url, exchange_code_for_tokens, get_userinfo

router = APIRouter(prefix="/auth", tags=["Social Login (Auth0)"])
logger = logging.getLogger("blog_api.social_auth")

# In-memory state store for CSRF protection on the OAuth redirect. Each
# entry expires after 10 minutes. A small dict is enough for this project's
# scale (SQLite, single process) - a production, multi-server deployment
# would use a shared store (e.g. Redis) instead.
_pending_states: dict[str, float] = {}
_STATE_TTL_SECONDS = 600


def _new_state() -> str:
    state = secrets.token_urlsafe(24)
    _pending_states[state] = time.time()
    # Opportunistic cleanup of expired entries.
    expired = [s for s, ts in _pending_states.items() if time.time() - ts > _STATE_TTL_SECONDS]
    for s in expired:
        _pending_states.pop(s, None)
    return state


def _consume_state(state: str) -> bool:
    ts = _pending_states.pop(state, None)
    if ts is None:
        return False
    return (time.time() - ts) <= _STATE_TTL_SECONDS


def _require_auth0_configured():
    if not settings.auth0_configured:
        raise HTTPException(
            status_code=503,
            detail="Social login isn't configured yet. Set AUTH0_DOMAIN, AUTH0_CLIENT_ID, "
                   "and AUTH0_CLIENT_SECRET in .env, then restart the server.",
        )


@router.get("/login/google")
def login_with_google():
    """Redirects the browser to Auth0's hosted login page, pre-selecting Google."""
    _require_auth0_configured()
    state = _new_state()
    return RedirectResponse(build_authorize_url("google-oauth2", state))


@router.get("/login/facebook")
def login_with_facebook():
    """Redirects the browser to Auth0's hosted login page, pre-selecting Facebook."""
    _require_auth0_configured()
    state = _new_state()
    return RedirectResponse(build_authorize_url("facebook", state))


def _unique_username(db: Session, base: str) -> str:
    """Turns an email's local part into a free username, e.g. 'baskar',
    'baskar2', 'baskar3', ... so social signups never collide with an
    existing username."""
    base = "".join(c for c in base.lower() if c.isalnum()) or "user"
    candidate = base
    suffix = 1
    while db.query(models.User).filter(models.User.username == candidate).first():
        suffix += 1
        candidate = f"{base}{suffix}"
    return candidate


@router.get("/callback")
def auth0_callback(
    code: str | None = Query(None),
    state: str | None = Query(None),
    error: str | None = Query(None),
    error_description: str | None = Query(None),
):
    """
    Auth0 redirects here after the person logs in (or cancels/fails) on
    its hosted page. On success, we exchange the code for a token, fetch
    the person's profile, create or update their row in our own users
    table, issue our own app JWT, and send the browser back to the
    frontend with that JWT attached as a URL fragment.
    """
    frontend = settings.FRONTEND_LOGIN_REDIRECT

    # Auth0 itself reported a problem (user cancelled, provider error, etc).
    if error:
        message = error_description or error
        return RedirectResponse(f"{frontend}?{urlencode({'auth_error': message})}")

    if not code or not state:
        return RedirectResponse(f"{frontend}?{urlencode({'auth_error': 'Missing callback details from Auth0'})}")

    if not _consume_state(state):
        return RedirectResponse(f"{frontend}?{urlencode({'auth_error': 'Login session expired or invalid. Please try again'})}")

    token_data = exchange_code_for_tokens(code)
    if not token_data or "access_token" not in token_data:
        return RedirectResponse(f"{frontend}?{urlencode({'auth_error': 'Could not verify login with the provider'})}")

    profile = get_userinfo(token_data["access_token"])
    if not profile or not profile.get("sub"):
        return RedirectResponse(f"{frontend}?{urlencode({'auth_error': 'Could not fetch your profile'})}")

    auth0_sub = profile["sub"]  # e.g. "google-oauth2|1029384756" or "facebook|1029384756"
    email = profile.get("email")
    name = profile.get("name") or (email.split("@")[0] if email else "user")
    picture = profile.get("picture")
    provider = "google" if auth0_sub.startswith("google") else "facebook" if auth0_sub.startswith("facebook") else "auth0"

    if not email:
        return RedirectResponse(
            f"{frontend}?{urlencode({'auth_error': f'Your {provider} account has no public email - please use email/password signup instead'})}"
        )

    db = SessionLocal()
    try:
        # First, look up by the stable Auth0 id (handles a returning social user).
        user = db.query(models.User).filter(models.User.auth0_sub == auth0_sub).first()

        if not user:
            # Not seen via this provider before - but maybe they already have a
            # local (email/password) account with the same email. Link it
            # rather than creating a duplicate account with the same email.
            user = db.query(models.User).filter(models.User.email == email).first()

        if not user:
            username = _unique_username(db, name)
            user = models.User(
                username=username,
                email=email,
                password=None,
                auth_provider=provider,
                auth0_sub=auth0_sub,
                avatar_url=picture,
            )
            basic_plan = db.query(models.SubscriptionPlan).filter(models.SubscriptionPlan.name == "basic").first()
            if basic_plan:
                user.plan_id = basic_plan.id
            db.add(user)
        else:
            # Existing user (first social login, or returning) - keep their
            # profile fresh and make sure this provider/sub is linked.
            user.auth0_sub = auth0_sub
            user.avatar_url = picture or user.avatar_url
            if user.auth_provider == "local" and not user.password:
                user.auth_provider = provider

        db.commit()
        db.refresh(user)

        access_token = create_access_token(data={"sub": str(user.id)})
        return RedirectResponse(
            f"{frontend}#token={access_token}&{urlencode({'username': user.username})}"
        )
    finally:
        db.close()
