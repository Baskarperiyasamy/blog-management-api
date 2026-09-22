from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user
from ..services.notification_service import notify_post_author
from ..plan_limits import enforce_like_limit

router = APIRouter(prefix="/posts", tags=["Likes"])


@router.post("/{post_id}/like", response_model=schemas.LikeStatus)
def like_post(
    post_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Like a post. Requires authentication. A user can only like a post once."""
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    existing = (
        db.query(models.Like)
        .filter(models.Like.post_id == post_id, models.Like.user_id == current_user.id)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already liked this post",
        )

    enforce_like_limit(db, current_user)

    like = models.Like(post_id=post_id, user_id=current_user.id)
    db.add(like)
    db.commit()

    # Email the post's author (runs in the background, after the response).
    notify_post_author(
        background_tasks,
        activity="like",
        post_title=post.title,
        author_email=post.author.email if post.author else None,
        author_id=post.author_id,
        actor_name=current_user.username,
        actor_id=current_user.id,
    )

    like_count = db.query(models.Like).filter(models.Like.post_id == post_id).count()
    return schemas.LikeStatus(liked=True, like_count=like_count)


@router.delete("/{post_id}/like", response_model=schemas.LikeStatus)
def unlike_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Remove your like from a post. Requires authentication."""
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    like = (
        db.query(models.Like)
        .filter(models.Like.post_id == post_id, models.Like.user_id == current_user.id)
        .first()
    )
    if not like:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have not liked this post",
        )

    db.delete(like)
    db.commit()

    like_count = db.query(models.Like).filter(models.Like.post_id == post_id).count()
    return schemas.LikeStatus(liked=False, like_count=like_count)
