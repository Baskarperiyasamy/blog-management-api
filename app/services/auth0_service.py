"""
services/auth0_service.py — talks to Auth0 for the two social login flows
(Google and Facebook). Everything else (issuing our own app JWT, creating/
updating the user row) stays in routers/social_auth.py so this file only
knows about Auth0's HTTP API.

Flow:
  1. build_authorize_url() - user's browser is sent here to log in with
     Google or Facebook, via Auth0's hosted login page.
  2. Auth0 redirects back to our own /auth/callback with a `code`.
  3. exchange_code_for_tokens() - swaps that code for an Auth0 access token.
  4. get_userinfo() - uses that access token to fetch the person's name,
     email, and picture from Auth0.
"""
import logging
from typing import Optional
from urllib.parse import urlencode

import httpx

from ..config import settings

logger = logging.getLogger("blog_api.auth0")


def build_authorize_url(connection: str, state: str) -> str:
    """
    connection: "google-oauth2" or "facebook"
    state: a random, unguessable string generated per login attempt and
    checked again in the callback, to prevent CSRF on the redirect.
    """
    params = {
        "response_type": "code",
        "client_id": settings.AUTH0_CLIENT_ID,
        "redirect_uri": settings.AUTH0_CALLBACK_URL,
        "scope": "openid profile email",
        "connection": connection,
        "state": state,
    }
    return f"https://{settings.AUTH0_DOMAIN}/authorize?{urlencode(params)}"


def exchange_code_for_tokens(code: str) -> Optional[dict]:
    """POSTs the authorization code to Auth0's /oauth/token endpoint.
    Returns the token response dict, or None on any failure."""
    try:
        response = httpx.post(
            f"https://{settings.AUTH0_DOMAIN}/oauth/token",
            json={
                "grant_type": "authorization_code",
                "client_id": settings.AUTH0_CLIENT_ID,
                "client_secret": settings.AUTH0_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.AUTH0_CALLBACK_URL,
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        logger.warning("Auth0 token exchange failed: %s", exc)
        return None


def get_userinfo(access_token: str) -> Optional[dict]:
    """Fetches the profile (sub, name, email, picture) for the token holder."""
    try:
        response = httpx.get(
            f"https://{settings.AUTH0_DOMAIN}/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        response.raise_for_status()
        return response.json()
    except Exception as exc:
        logger.warning("Auth0 userinfo fetch failed: %s", exc)
        return None
