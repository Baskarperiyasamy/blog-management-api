from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user
from ..email_utils import send_email_notification

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

    like = models.Like(post_id=post_id, user_id=current_user.id)
    db.add(like)
    db.commit()

    if post.author and post.author_id != current_user.id:
        background_tasks.add_task(
            send_email_notification,
            post.author.email,
            "New like on your post",
            f"{current_user.username} liked your post '{post.title}'",
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
