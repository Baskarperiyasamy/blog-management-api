"""
services/notification_service.py — decides WHAT a notification says and
WHETHER it should be sent, for two channels:

  1. Email (via SMTP) — notify_post_author(), unchanged from before.
  2. In-app (bell-icon Notification Center) — create_in_app_notification()
     and its activity-specific wrappers below. These write a row to the
     `notifications` table; they do not touch email or SMTP at all.

Both channels are independent — a call site can use one, the other, or
both (see routers/likes.py, routers/comments.py, routers/subscriptions.py).
"""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from .. import models
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


# ---------------------------------------------------------------------------
# In-app Notification Center (bell icon)
# ---------------------------------------------------------------------------
def create_in_app_notification(
    db: Session,
    *,
    user_id: int,
    message: str,
    notification_type: str,
    actor_id: int | None = None,
    post_id: int | None = None,
) -> models.Notification:
    """Writes one row to the notifications table. Does NOT commit — the
    caller's existing db.commit() (e.g. after creating the Like/Comment)
    covers this too, so the notification and the action it describes are
    always saved together or not at all."""
    notification = models.Notification(
        user_id=user_id,
        actor_id=actor_id,
        post_id=post_id,
        notification_type=notification_type,
        message=message,
    )
    db.add(notification)
    return notification


def notify_post_author_in_app(
    db: Session,
    *,
    activity: str,          # "like" or "comment"
    post_id: int,
    post_title: str,
    author_id: int,
    actor_name: str,
    actor_id: int,
) -> models.Notification | None:
    """In-app equivalent of notify_post_author() (email). Skipped when the
    author is acting on their own post, same rule as the email version."""
    if author_id == actor_id and not settings.NOTIFY_ON_OWN_ACTIVITY:
        return None

    verb = "commented on" if activity == "comment" else "liked"
    message = f'{actor_name} {verb} your post "{post_title}"'

    return create_in_app_notification(
        db,
        user_id=author_id,
        message=message,
        notification_type=activity,
        actor_id=actor_id,
        post_id=post_id,
    )


def notify_subscription_activated_in_app(
    db: Session,
    *,
    user_id: int,
    plan_name: str,
    is_renewal: bool,
) -> models.Notification:
    """Fires when a user's own subscription is activated or renewed."""
    verb = "renewed" if is_renewal else "activated"
    message = f'Your "{plan_name.title()}" subscription has been {verb}.'
    return create_in_app_notification(
        db,
        user_id=user_id,
        message=message,
        notification_type="subscription",
    )
