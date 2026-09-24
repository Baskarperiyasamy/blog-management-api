"""
services/ai_support_service.py — decides what the AI Support Chat replies.

Two modes:
  1. Mocked FAQ mode (default, no setup required): matches the user's
     message against keyword lists for each supported topic and returns a
     predefined answer. This is what runs out of the box.
  2. OpenAI mode (optional): if OPENAI_API_KEY is set in .env, the message
     is forwarded to the OpenAI Chat Completions API instead. If that call
     fails for any reason (bad key, network, rate limit), it falls back to
     the mocked FAQ answer rather than erroring out to the user.

Either way every exchange is logged by the caller (routers/ai_support.py)
into the chat_logs table.
"""
import logging
from typing import Optional

from ..config import settings

logger = logging.getLogger("blog_api.ai_support")

# ---------------------------------------------------------------------------
# Mocked FAQ knowledge base
# ---------------------------------------------------------------------------
# Each topic: (keywords to match in the user's message, canned reply).
# Matching is simple substring/keyword scoring - good enough for an FAQ
# bot and needs no external dependency.
FAQ_TOPICS = [
    (
        "create_post",
        ["create post", "new post", "write post", "add post", "how to post", "publish post"],
        "To create a post, log in and send a POST request to /posts with a title, "
        "content, and an optional cover image. In the dashboard or Swagger UI (/docs), "
        "open POST /posts, fill in the fields, and click Execute.",
    ),
    (
        "edit_delete_post",
        ["edit post", "update post", "delete post", "remove post", "change post"],
        "You can edit your own post with PUT /posts/{post_id}, or remove it with "
        "DELETE /posts/{post_id}. Only the post's original author is allowed to edit "
        "or delete it - you'll get a 403 error if you try on someone else's post.",
    ),
    (
        "subscription",
        ["subscription", "subscribe", "plan", "upgrade", "premium", "pro plan", "basic plan"],
        "Subscriptions control how many posts, images, likes, and comments you can use "
        "per month. Every new account starts on the Basic plan automatically. You can "
        "view available plans with GET /subscriptions/plans and switch or renew with "
        "POST /subscriptions/subscribe.",
    ),
    (
        "billing",
        ["billing", "invoice", "payment", "receipt", "transaction", "charge", "refund"],
        "Your billing history and invoices are available at GET /subscriptions/history. "
        "Each entry includes the transaction ID, amount, plan, and a downloadable invoice "
        "PDF. This is currently a sandbox billing system - no real payments are processed.",
    ),
    (
        "profile",
        ["profile", "account", "username", "email address", "change password", "my account"],
        "Profile and account details are tied to your registered username and email from "
        "sign-up. Password changes and profile-editing endpoints depend on what's enabled "
        "in this build - check /docs for the latest available account endpoints.",
    ),
    (
        "dashboard",
        ["dashboard", "analytics", "statistics", "stats", "chart", "graph", "views"],
        "Your personal dashboard is at GET /user/dashboard (or the visual version at "
        "/static/dashboard.html). It shows your total posts, comments made, likes "
        "received, and post views, plus bar, pie, and line charts built from that data. "
        "It only ever shows your own activity.",
    ),
    (
        "notifications",
        ["notification", "bell icon", "alert", "unread"],
        "The notification bell shows alerts when someone likes or comments on your posts, "
        "or when your subscription is activated or renewed. Check it via GET /notifications, "
        "or click the bell icon on the dashboard page. Click a notification, or use "
        "'Mark all as read', to clear it.",
    ),
    (
        "login_auth",
        ["login", "log in", "sign in", "token", "jwt", "authoriz", "register", "sign up"],
        "Register with POST /auth/register, then log in with POST /auth/login to receive "
        "a JWT access token. Include it as 'Authorization: Bearer <token>' on any "
        "request that needs authentication, or paste it into Swagger's Authorize button.",
    ),
]

FALLBACK_REPLY = (
    "I'm not totally sure about that one yet, but here's what I can help with: "
    "creating or editing posts, subscriptions and billing, your dashboard analytics, "
    "notifications, and logging in. Try asking about one of those, or check the full "
    "API list at /docs."
)

GREETING_KEYWORDS = ["hi", "hello", "hey", "good morning", "good evening"]
GREETING_REPLY = (
    "Hi! I'm the platform's support assistant. I can help with creating posts, "
    "subscriptions and billing, your dashboard, notifications, or logging in - "
    "what do you need a hand with?"
)


def _match_faq(message: str) -> tuple[Optional[str], Optional[str]]:
    """Returns (topic, reply) for the best keyword match, or (None, None)."""
    text = message.lower().strip()

    if any(g in text for g in GREETING_KEYWORDS) and len(text) < 30:
        return "greeting", GREETING_REPLY

    best_topic, best_reply, best_score = None, None, 0
    for topic, keywords, reply in FAQ_TOPICS:
        score = sum(1 for kw in keywords if kw in text)
        if score > best_score:
            best_topic, best_reply, best_score = topic, reply, score

    if best_score > 0:
        return best_topic, best_reply
    return None, None


def get_mocked_reply(message: str) -> tuple[str, Optional[str]]:
    """Always succeeds - this is the guaranteed fallback. Returns (reply, topic)."""
    topic, reply = _match_faq(message)
    if reply:
        return reply, topic
    return FALLBACK_REPLY, None


def get_openai_reply(message: str) -> Optional[str]:
    """Tries the real OpenAI API. Returns None (never raises) on any failure
    so the caller can fall back to the mocked reply."""
    if not settings.openai_configured:
        return None
    try:
        import httpx

        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
            json={
                "model": settings.OPENAI_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a concise support assistant for a blog platform API. "
                            "Help with posts, subscriptions, billing, dashboard analytics, "
                            "notifications, and account/login questions. Keep answers short."
                        ),
                    },
                    {"role": "user", "content": message},
                ],
                "max_tokens": 200,
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception as exc:  # network error, bad key, rate limit, etc.
        logger.warning("OpenAI call failed, falling back to mocked reply: %s", exc)
        return None


def get_ai_reply(message: str) -> tuple[str, Optional[str], str]:
    """
    Main entry point. Returns (reply, matched_topic, source).
    source is "openai" if the real API answered, otherwise "mocked".
    """
    if settings.openai_configured:
        openai_reply = get_openai_reply(message)
        if openai_reply:
            return openai_reply, None, "openai"

    reply, topic = get_mocked_reply(message)
    return reply, topic, "mocked"
