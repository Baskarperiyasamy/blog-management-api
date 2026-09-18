from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .database import Base, engine, SessionLocal
from . import models  # noqa: F401  (ensures models are registered before create_all)
from .media_utils import ensure_media_dirs
from .invoice_utils import ensure_invoice_dir
from .routers import auth, posts, comments, likes, subscriptions

# Creates blog.db and all tables automatically on first run.
Base.metadata.create_all(bind=engine)

# Creates media/posts/ and media/invoices/ so uploads/invoices have somewhere to land.
ensure_media_dirs()
ensure_invoice_dir()


def seed_subscription_plans() -> None:
    """
    Seeds the 3 fixed plans exactly once. There is no create-plan endpoint
    since the task specifies a fixed catalog of three plan types.
    """
    db = SessionLocal()
    try:
        if db.query(models.SubscriptionPlan).count() > 0:
            return  # already seeded

        plans = [
            models.SubscriptionPlan(
                name="basic", price=0.0, duration_days=30,
                max_posts=1, max_images_per_post=1, max_likes=5, max_comments=5,
            ),
            models.SubscriptionPlan(
                name="premium", price=9.99, duration_days=30,
                max_posts=2, max_images_per_post=2, max_likes=20, max_comments=20,
            ),
            models.SubscriptionPlan(
                name="pro", price=29.99, duration_days=30,
                max_posts=None, max_images_per_post=None, max_likes=None, max_comments=None,
            ),
        ]
        db.add_all(plans)
        db.commit()
    finally:
        db.close()


seed_subscription_plans()

app = FastAPI(
    title="Blog Management API",
    description=(
        "A mini blogging system: authenticated users can create/update/delete "
        "their own posts (with optional cover images), comment on posts, "
        "like/unlike posts, paginate/search the post feed, trigger email "
        "notifications on new comments and likes, and subscribe to a "
        "Basic/Premium/Pro plan that gates how much of each feature they can use."
    ),
    version="3.0.0",
)

# Serves uploaded images and invoice PDFs at http://<host>/media/...
app.mount("/media", StaticFiles(directory="media"), name="media")

app.include_router(auth.router)
app.include_router(posts.router)
app.include_router(comments.router)
app.include_router(likes.router)
app.include_router(subscriptions.router)


@app.get("/", tags=["Health"])
def root():
    return {"message": "Blog Management API is running. Visit /docs for Swagger UI."}
