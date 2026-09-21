from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user
<<<<<<< HEAD
from ..services.notification_service import notify_post_author
from ..plan_limits import enforce_comment_limit
=======
from ..email_utils import send_email_notification
<<<<<<< HEAD
from ..plan_limits import enforce_comment_limit
=======
>>>>>>> origin/main
>>>>>>> f4a61c9de3181091724c61d126cb113a3c69516f

router = APIRouter(prefix="/posts", tags=["Comments"])


@router.post(
    "/{post_id}/comments",
    response_model=schemas.CommentOut,
    status_code=status.HTTP_201_CREATED,
)
def add_comment(
    post_id: int,
    comment_in: schemas.CommentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Add a comment to a post. Requires authentication."""
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

<<<<<<< HEAD
    enforce_comment_limit(db, current_user)

=======
<<<<<<< HEAD
    enforce_comment_limit(db, current_user)

=======
>>>>>>> origin/main
>>>>>>> f4a61c9de3181091724c61d126cb113a3c69516f
    comment = models.Comment(
        post_id=post_id, user_id=current_user.id, text=comment_in.text
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

<<<<<<< HEAD
    # Email the post's author (runs in the background, after the response).
    notify_post_author(
        background_tasks,
        activity="comment",
        post_title=post.title,
        author_email=post.author.email if post.author else None,
        author_id=post.author_id,
        actor_name=current_user.username,
        actor_id=current_user.id,
    )
=======
    # Notify the post's author (unless they commented on their own post).
    if post.author and post.author_id != current_user.id:
        background_tasks.add_task(
            send_email_notification,
            post.author.email,
            "New comment on your post",
            f"{current_user.username} commented on '{post.title}': {comment_in.text}",
        )
>>>>>>> f4a61c9de3181091724c61d126cb113a3c69516f

    return schemas.CommentOut(
        id=comment.id,
        post_id=comment.post_id,
        user_id=comment.user_id,
        text=comment.text,
        created_at=comment.created_at,
        username=current_user.username,
    )


@router.get("/{post_id}/comments", response_model=List[schemas.CommentOut])
def list_comments(post_id: int, db: Session = Depends(get_db)):
    """Public endpoint - anyone can view the comments on a post."""
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    comments = (
        db.query(models.Comment)
        .filter(models.Comment.post_id == post_id)
        .order_by(models.Comment.created_at.asc())
        .all()
    )
    return [
        schemas.CommentOut(
            id=c.id,
            post_id=c.post_id,
            user_id=c.user_id,
            text=c.text,
            created_at=c.created_at,
            username=c.user.username if c.user else None,
        )
        for c in comments
    ]
