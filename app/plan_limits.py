from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from . import models

LIMIT_EXCEEDED_MESSAGE = "You've reached your plan limit. Kindly upgrade your plan to continue."


def get_active_plan(db: Session, user: models.User) -> models.SubscriptionPlan:
    """
    Every user has an active plan (assigned automatically at registration -
    see auth.py). This falls back to the Basic plan defensively in case a
    user somehow has no plan_id set.
    """
    if user.plan_id:
        plan = (
            db.query(models.SubscriptionPlan)
            .filter(models.SubscriptionPlan.id == user.plan_id)
            .first()
        )
        if plan:
            return plan

    basic = (
        db.query(models.SubscriptionPlan)
        .filter(models.SubscriptionPlan.name == "basic")
        .first()
    )
    if not basic:
        # Should never happen - plans are seeded at startup.
        raise HTTPException(status_code=500, detail="No subscription plans configured.")
    return basic


def _enforce(current_count: int, limit: int | None):
    if limit is not None and current_count >= limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=LIMIT_EXCEEDED_MESSAGE
        )


def enforce_post_limit(db: Session, user: models.User) -> None:
    plan = get_active_plan(db, user)
    count = db.query(models.Post).filter(models.Post.author_id == user.id).count()
    _enforce(count, plan.max_posts)


def enforce_image_limit(db: Session, user: models.User) -> None:
    """
    NOTE: the Post model (from the previous milestone) supports one cover
    image per post. So "images per post" is enforced here as the total
    number of images the user has uploaded across all their posts, which
    is the closest honest equivalent without adding a third model (the
    task specifies exactly two new models: SubscriptionPlan and
    BillingHistory).
    """
    plan = get_active_plan(db, user)
    count = (
        db.query(models.Post)
        .filter(models.Post.author_id == user.id, models.Post.image.isnot(None))
        .count()
    )
    _enforce(count, plan.max_images_per_post)


def enforce_like_limit(db: Session, user: models.User) -> None:
    plan = get_active_plan(db, user)
    count = db.query(models.Like).filter(models.Like.user_id == user.id).count()
    _enforce(count, plan.max_likes)


def enforce_comment_limit(db: Session, user: models.User) -> None:
    plan = get_active_plan(db, user)
    count = db.query(models.Comment).filter(models.Comment.user_id == user.id).count()
    _enforce(count, plan.max_comments)
