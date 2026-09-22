from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user

router = APIRouter(prefix="/user/dashboard", tags=["Dashboard"])


@router.get("", response_model=schemas.DashboardSummary)
def get_my_dashboard(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Returns the authenticated user's own activity statistics and analytics:
    - total posts created
    - total comments made (by this user, on any post)
    - total likes received (on this user's posts)
    - total comments received (on this user's posts)
    - total views (on this user's posts)
    - per-post breakdown (for bar/pie charts)
    - daily activity over the last `days` days (for the line chart)

    A user can only ever see their own data - there is no user_id param,
    the identity comes entirely from the JWT (get_current_user).
    """
    user_id = current_user.id

    my_posts = db.query(models.Post).filter(models.Post.author_id == user_id).all()
    post_ids = [p.id for p in my_posts]

    total_posts = len(my_posts)

    total_comments_made = (
        db.query(models.Comment).filter(models.Comment.user_id == user_id).count()
    )

    if post_ids:
        total_likes_received = (
            db.query(models.Like).filter(models.Like.post_id.in_(post_ids)).count()
        )
        total_comments_received = (
            db.query(models.Comment).filter(models.Comment.post_id.in_(post_ids)).count()
        )
        total_views = (
            db.query(models.PostView).filter(models.PostView.post_id.in_(post_ids)).count()
        )
    else:
        total_likes_received = 0
        total_comments_received = 0
        total_views = 0

    # ---- per-post breakdown (bar / pie chart source) ----
    per_post_stats = []
    for post in my_posts:
        likes = db.query(models.Like).filter(models.Like.post_id == post.id).count()
        comments = db.query(models.Comment).filter(models.Comment.post_id == post.id).count()
        views = db.query(models.PostView).filter(models.PostView.post_id == post.id).count()
        per_post_stats.append(
            schemas.PostStat(
                post_id=post.id,
                title=post.title,
                likes=likes,
                comments=comments,
                views=views,
                created_at=post.created_at,
            )
        )
    per_post_stats.sort(key=lambda s: s.likes, reverse=True)

    # ---- activity over time (line chart source) ----
    since = datetime.utcnow() - timedelta(days=days)
    day_buckets = defaultdict(lambda: {"posts": 0, "comments": 0, "likes": 0})

    for p in my_posts:
        if p.created_at and p.created_at >= since:
            day_buckets[p.created_at.date().isoformat()]["posts"] += 1

    my_comments = (
        db.query(models.Comment)
        .filter(models.Comment.user_id == user_id, models.Comment.created_at >= since)
        .all()
    )
    for c in my_comments:
        day_buckets[c.created_at.date().isoformat()]["comments"] += 1

    # Note: the Like model has no timestamp column (see models.py), so
    # "likes over time" can't be charted daily - likes are instead shown
    # per-post in the bar/pie chart above. The line chart covers posts +
    # comments over time, which both have created_at.

    activity_over_time = [
        schemas.ActivityPoint(date=day, posts=v["posts"], comments=v["comments"], likes=v["likes"])
        for day, v in sorted(day_buckets.items())
    ]

    return schemas.DashboardSummary(
        username=current_user.username,
        total_posts=total_posts,
        total_comments_made=total_comments_made,
        total_likes_received=total_likes_received,
        total_comments_received=total_comments_received,
        total_views=total_views,
        per_post_stats=per_post_stats,
        activity_over_time=activity_over_time,
    )


@router.post("/view/{post_id}", status_code=204)
def record_post_view(
    post_id: int,
    db: Session = Depends(get_db),
):
    """
    Records a view of a post (call this from the post-detail page/endpoint).
    Anonymous views are allowed - this endpoint does NOT require auth so
    that page views can be tracked regardless of login state.
    """
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    db.add(models.PostView(post_id=post_id))
    db.commit()
    return None


@router.get("/page", response_class=HTMLResponse, include_in_schema=False)
def dashboard_page():
    """
    Serves the static Chart.js dashboard HTML page. The page itself calls
    GET /user/dashboard with the JWT (entered once, stored in memory) and
    renders the charts client-side - see /static/dashboard.html.
    """
    with open("static/dashboard.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())
