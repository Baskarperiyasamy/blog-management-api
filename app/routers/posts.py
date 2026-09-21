import math
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user
from ..media_utils import delete_post_image, image_url_for, save_post_image
from ..plan_limits import enforce_image_limit, enforce_post_limit

router = APIRouter(prefix="/posts", tags=["Posts"])


def _serialize_post(db: Session, post: models.Post) -> schemas.PostOut:
    like_count = db.query(models.Like).filter(models.Like.post_id == post.id).count()
    comment_count = (
        db.query(models.Comment).filter(models.Comment.post_id == post.id).count()
    )
    return schemas.PostOut(
        id=post.id,
        title=post.title,
        content=post.content,
        author_id=post.author_id,
        created_at=post.created_at,
        author_username=post.author.username if post.author else None,
        image_url=image_url_for(post.image),
        like_count=like_count,
        comment_count=comment_count,
    )


def _get_owned_post(db: Session, post_id: int, current_user: models.User) -> models.Post:
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only modify your own posts",
        )
    return post


# ---------------------------------------------------------------------------
# CREATE  (multipart/form-data so an optional image file can be attached)
# ---------------------------------------------------------------------------
def _create_post(
    title: str = Form(..., min_length=3, max_length=200),
    content: str = Form(..., min_length=1),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # Plan-based access control: post count, and image count if attaching one.
    enforce_post_limit(db, current_user)
    if image is not None and image.filename:
        enforce_image_limit(db, current_user)

    image_path = save_post_image(image) if image is not None and image.filename else None

    post = models.Post(
        title=title, content=content, author_id=current_user.id, image=image_path
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return _serialize_post(db, post)


# Primary RESTful route
router.add_api_route(
    "", _create_post, methods=["POST"], response_model=schemas.PostOut,
    status_code=status.HTTP_201_CREATED, name="create_post",
    summary="Create Post",
    description="Create a new blog post. Accepts multipart/form-data: title, "
                 "content, and an optional image file. Requires authentication.",
)
# Alias matching the assignment spec: POST /posts/create
router.add_api_route(
    "/create", _create_post, methods=["POST"], response_model=schemas.PostOut,
    status_code=status.HTTP_201_CREATED, name="create_post_alias",
    summary="Create Post (alias)",
    description="Identical to POST /posts — provided to match the /posts/create spec.",
)


# ---------------------------------------------------------------------------
# LIST  (pagination + search)
# ---------------------------------------------------------------------------
@router.get("", response_model=schemas.PaginatedPosts)
def list_posts(
    page: int = Query(1, ge=1, description="Page number, starting at 1"),
    limit: int = Query(10, ge=1, le=100, description="Posts per page (max 100)"),
    search: Optional[str] = Query(
        None, description="Filter posts where title or content contains this text"
    ),
    db: Session = Depends(get_db),
):
    """Public endpoint. Supports GET /posts?page=1&limit=10&search=keyword."""
    query = db.query(models.Post)

    if search:
        like_pattern = f"%{search}%"
        query = query.filter(
            or_(models.Post.title.ilike(like_pattern), models.Post.content.ilike(like_pattern))
        )

    total = query.count()
    total_pages = math.ceil(total / limit) if total else 0

    posts = (
        query.order_by(models.Post.created_at.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )

    return schemas.PaginatedPosts(
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
        results=[_serialize_post(db, p) for p in posts],
    )


@router.get("/mine", response_model=List[schemas.PostOut])
def my_posts(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Return only the posts belonging to the logged-in user."""
    posts = (
        db.query(models.Post)
        .filter(models.Post.author_id == current_user.id)
        .order_by(models.Post.created_at.desc())
        .all()
    )
    return [_serialize_post(db, p) for p in posts]


@router.get("/{post_id}", response_model=schemas.PostDetailOut)
def get_post(post_id: int, db: Session = Depends(get_db)):
    """Public endpoint - view a single post along with its comments."""
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    like_count = db.query(models.Like).filter(models.Like.post_id == post.id).count()
    comments = (
        db.query(models.Comment)
        .filter(models.Comment.post_id == post.id)
        .order_by(models.Comment.created_at.asc())
        .all()
    )
    comments_out = [
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

    return schemas.PostDetailOut(
        id=post.id,
        title=post.title,
        content=post.content,
        author_id=post.author_id,
        created_at=post.created_at,
        author_username=post.author.username if post.author else None,
        image_url=image_url_for(post.image),
        like_count=like_count,
        comment_count=len(comments),
        comments=comments_out,
    )


# ---------------------------------------------------------------------------
# UPDATE  (multipart/form-data, all fields optional; owner only)
# ---------------------------------------------------------------------------
def _update_post(
    post_id: int,
    title: Optional[str] = Form(None, min_length=3, max_length=200),
    content: Optional[str] = Form(None, min_length=1),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    post = _get_owned_post(db, post_id, current_user)

    if title is not None:
        post.title = title
    if content is not None:
        post.content = content
    if image is not None and image.filename:
        if post.image is None:
            # Only counts against the plan limit if this post didn't already
            # have an image - replacing an existing one isn't a net-new image.
            enforce_image_limit(db, current_user)
        new_path = save_post_image(image)
        delete_post_image(post.image)  # remove the old file, if any
        post.image = new_path

    db.commit()
    db.refresh(post)
    return _serialize_post(db, post)


# Primary RESTful route
router.add_api_route(
    "/{post_id}", _update_post, methods=["PUT"], response_model=schemas.PostOut,
    name="update_post",
    summary="Update Post",
    description="Update a post. Accepts multipart/form-data: title, content, "
                 "and/or a replacement image. Only the post's owner is allowed to do this.",
)
# Alias matching the assignment spec: PUT /posts/{id}/update
router.add_api_route(
    "/{post_id}/update", _update_post, methods=["PUT"], response_model=schemas.PostOut,
    name="update_post_alias",
    summary="Update Post (alias)",
    description="Identical to PUT /posts/{post_id} — provided to match the /posts/{id}/update spec.",
)


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Delete a post (and its image file, if any). Only the post's owner is allowed to do this."""
    post = _get_owned_post(db, post_id, current_user)
    delete_post_image(post.image)
    db.delete(post)
    db.commit()
    return None
