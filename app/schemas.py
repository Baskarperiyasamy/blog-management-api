from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ---------------------------------------------------------------------------
# User / Auth
# ---------------------------------------------------------------------------
class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=100)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------------------------------------------------------------------------
# Comment
# ---------------------------------------------------------------------------
class CommentCreate(BaseModel):
    text: str = Field(min_length=1, max_length=1000)


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    post_id: int
    user_id: int
    text: str
    created_at: datetime
    username: Optional[str] = None


# ---------------------------------------------------------------------------
# Like
# ---------------------------------------------------------------------------
class LikeStatus(BaseModel):
    liked: bool
    like_count: int


# ---------------------------------------------------------------------------
# Post
# ---------------------------------------------------------------------------
class PostCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    content: str = Field(min_length=1)


class PostUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=3, max_length=200)
    content: Optional[str] = Field(default=None, min_length=1)


class PostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    author_id: int
    created_at: datetime
    author_username: Optional[str] = None
    image_url: Optional[str] = None
    like_count: int = 0
    comment_count: int = 0


class PostDetailOut(PostOut):
    comments: List[CommentOut] = []


class PaginatedPosts(BaseModel):
    total: int
    page: int
    limit: int
    total_pages: int
    results: List[PostOut]


# ---------------------------------------------------------------------------
# Subscription / Billing
# ---------------------------------------------------------------------------
class SubscriptionPlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price: float
    duration_days: int
    max_posts: Optional[int] = None
    max_images_per_post: Optional[int] = None
    max_likes: Optional[int] = None
    max_comments: Optional[int] = None


class SubscribeRequest(BaseModel):
    plan_name: str = Field(description="One of: basic, premium, pro")


class BillingHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    plan_id: int
    plan_name: Optional[str] = None
    transaction_id: str
    amount: float
    start_date: datetime
    end_date: datetime
    invoice_url: Optional[str] = None
    created_at: datetime


class MyPlanUsage(BaseModel):
    posts_used: int
    posts_limit: Optional[int]
    images_used: int
    images_limit: Optional[int]
    likes_used: int
    likes_limit: Optional[int]
    comments_used: int
    comments_limit: Optional[int]


class MyPlanOut(BaseModel):
    plan: SubscriptionPlanOut
    usage: MyPlanUsage


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------
class PostStat(BaseModel):
    post_id: int
    title: str
    likes: int
    comments: int
    views: int
    created_at: datetime


class ActivityPoint(BaseModel):
    date: str  # "YYYY-MM-DD"
    posts: int
    comments: int
    likes: int


class DashboardSummary(BaseModel):
    username: str
    total_posts: int
    total_comments_made: int
    total_likes_received: int
    total_comments_received: int
    total_views: int
    per_post_stats: List[PostStat]
    activity_over_time: List[ActivityPoint]
<<<<<<< HEAD


# ---------------------------------------------------------------------------
# In-app Notification Center
# ---------------------------------------------------------------------------
class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    notification_type: str
    message: str
    is_read: bool
    post_id: Optional[int] = None
    created_at: datetime


class NotificationListOut(BaseModel):
    unread_count: int
    notifications: List[NotificationOut]


class MarkReadOut(BaseModel):
    id: int
    is_read: bool


class MarkAllReadOut(BaseModel):
    marked_read: int
=======
>>>>>>> 403a1134133178c9857fb7d9cd5b11da2db05a74
