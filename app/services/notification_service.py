"""
services/notification_service.py — decides WHAT a notification says and
WHETHER it should be sent. It does not talk to SMTP (email_service does) and
does not touch the database.

The main entry point, notify_post_author(), is called from the comment and
like endpoints; it queues the email with FastAPI BackgroundTasks so the API
response is never delayed.
"""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from fastapi import BackgroundTasks

from ..config import settings
from .email_service import send_email


def _now_local() -> datetime:
    try:
        return datetime.now(ZoneInfo(settings.TIMEZONE))
    except Exception:  # unknown tz name / tzdata missing
        return datetime.now(timezone.utc)


def _build_message(post_title: str, actor_name: str, activity_label: str,
                   timestamp: datetime) -> tuple[str, str]:
    """(subject, body) in the exact format from the brief:

        Post: "FastAPI Best Practices"
        User: John Doe
        Activity: Commented on your post
        Time: 2026-03-04 11:20 AM
    """
    noun = "comment" if activity_label == "Commented" else "like"
    subject = f"New {noun} on your post: {post_title}"
    body = (
        f'Post: "{post_title}"\n'
        f"User: {actor_name}\n"
        f"Activity: {activity_label} on your post\n"
        f"Time: {timestamp.strftime('%Y-%m-%d %I:%M %p')}"
    )
    return subject, body


def build_comment_notification(post_title: str, commenter_name: str,
                               timestamp: datetime | None = None) -> tuple[str, str]:
    return _build_message(post_title, commenter_name, "Commented", timestamp or _now_local())


def build_like_notification(post_title: str, liker_name: str,
                            timestamp: datetime | None = None) -> tuple[str, str]:
    return _build_message(post_title, liker_name, "Liked", timestamp or _now_local())


def notify_post_author(
    background_tasks: BackgroundTasks,
    *,
    activity: str,          # "comment" or "like"
    post_title: str,
    author_email: str | None,
    author_id: int,
    actor_name: str,
    actor_id: int,
) -> bool:
    """Queues an email to the post's author. Returns True if it was queued.

    Skipped when the author has no email, or when the author is acting on
    their own post (unless NOTIFY_ON_OWN_ACTIVITY=true in .env).
    """
    if not author_email:
        return False
    if author_id == actor_id and not settings.NOTIFY_ON_OWN_ACTIVITY:
        return False

    if activity == "comment":
        subject, body = build_comment_notification(post_title, actor_name)
    elif activity == "like":
        subject, body = build_like_notification(post_title, actor_name)
    else:
        raise ValueError(f"Unknown activity: {activity}")

    background_tasks.add_task(send_email, author_email, subject, body)
    return True
