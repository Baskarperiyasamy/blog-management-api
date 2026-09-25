from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    Boolean,
    ForeignKey,
    DateTime,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    # Nullable: social-login-only accounts (Google/Facebook) have no local
    # password - they authenticate entirely through Auth0.
    password = Column(String(255), nullable=True)  # stores the HASHED password
    auth_provider = Column(String(20), nullable=False, default="local")  # "local" | "google" | "facebook"
    auth0_sub = Column(String(120), unique=True, index=True, nullable=True)  # Auth0's stable user id, e.g. "google-oauth2|12345"
    avatar_url = Column(String(500), nullable=True)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    posts = relationship(
        "Post", back_populates="author", cascade="all, delete-orphan"
    )
    comments = relationship(
        "Comment", back_populates="user", cascade="all, delete-orphan"
    )
    likes = relationship(
        "Like", back_populates="user", cascade="all, delete-orphan"
    )
    plan = relationship("SubscriptionPlan", back_populates="users")
    billing_history = relationship(
        "BillingHistory", back_populates="user", cascade="all, delete-orphan"
    )
    notifications = relationship(
        "Notification",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="Notification.user_id",
    )


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    image = Column(String(255), nullable=True)  # relative path under /media, e.g. "posts/xyz.jpg"
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    author = relationship("User", back_populates="posts")
    comments = relationship(
        "Comment", back_populates="post", cascade="all, delete-orphan"
    )
    likes = relationship(
        "Like", back_populates="post", cascade="all, delete-orphan"
    )
    views = relationship(
        "PostView", back_populates="post", cascade="all, delete-orphan"
    )


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    post = relationship("Post", back_populates="comments")
    user = relationship("User", back_populates="comments")


class Like(Base):
    __tablename__ = "likes"
    __table_args__ = (
        UniqueConstraint("post_id", "user_id", name="unique_post_like"),
    )

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    post = relationship("Post", back_populates="likes")
    user = relationship("User", back_populates="likes")


class PostView(Base):
    """One row per post view (anonymous or authenticated). Used for the
    'Total post views' stat and the activity-over-time chart."""
    __tablename__ = "post_views"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    viewer_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # nullable: anonymous views allowed
    viewed_at = Column(DateTime, default=datetime.utcnow)

    post = relationship("Post", back_populates="views")


class Notification(Base):
    """An in-app alert for a user (bell-icon notification center). Created
    automatically when someone likes/comments on the user's post, or when
    the user's own subscription is activated/renewed."""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # recipient
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # who triggered it (null for system events)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=True)   # related post, if any
    notification_type = Column(String(20), nullable=False)  # "like" | "comment" | "subscription"
    message = Column(String(255), nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications", foreign_keys=[user_id])


class ChatLog(Base):
    """One row per AI Support Chat exchange, for the activity-tracking
    requirement (user, question, AI response, timestamp)."""
    __tablename__ = "chat_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # nullable: anonymous chat allowed
    question = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    matched_topic = Column(String(50), nullable=True)  # which FAQ topic matched, if any
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")


class SubscriptionPlan(Base):
    """
    Catalog of the 3 fixed plans (basic / premium / pro). Seeded once at
    startup (see main.py) - there is no create-plan endpoint since the
    task specifies exactly three fixed plan types.

    A limit column of NULL means "unlimited" (used for the Pro plan).
    """
    __tablename__ = "subscription_plans"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)  # "basic" | "premium" | "pro"
    price = Column(Float, nullable=False)
    duration_days = Column(Integer, nullable=False, default=30)

    max_posts = Column(Integer, nullable=True)             # None = unlimited
    max_images_per_post = Column(Integer, nullable=True)   # None = unlimited
    max_likes = Column(Integer, nullable=True)              # None = unlimited
    max_comments = Column(Integer, nullable=True)           # None = unlimited

    users = relationship("User", back_populates="plan")
    billing_history = relationship("BillingHistory", back_populates="plan")


class BillingHistory(Base):
    """One row per subscription/renewal event, with its generated invoice."""
    __tablename__ = "billing_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=False)

    transaction_id = Column(String(50), unique=True, nullable=False)
    amount = Column(Float, nullable=False)  # snapshot of the plan price paid
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    invoice_path = Column(String(255), nullable=True)  # relative path under /media
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="billing_history")
    plan = relationship("SubscriptionPlan", back_populates="billing_history")
