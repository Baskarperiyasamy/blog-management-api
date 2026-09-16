from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .database import Base, engine
from . import models  # noqa: F401  (ensures models are registered before create_all)
from .media_utils import ensure_media_dirs
from .routers import auth, posts, comments, likes

# Creates blog.db and all tables automatically on first run.
Base.metadata.create_all(bind=engine)

# Creates media/posts/ so uploaded images have somewhere to land.
ensure_media_dirs()

app = FastAPI(
    title="Blog Management API",
    description=(
        "A mini blogging system: authenticated users can create/update/delete "
        "their own posts (with optional cover images), comment on posts, "
        "like/unlike posts, paginate/search the post feed, and trigger email "
        "notifications on new comments and likes."
    ),
    version="2.0.0",
)

# Serves uploaded images at http://<host>/media/posts/<filename>
app.mount("/media", StaticFiles(directory="media"), name="media")

app.include_router(auth.router)
app.include_router(posts.router)
app.include_router(comments.router)
app.include_router(likes.router)


@app.get("/", tags=["Health"])
def root():
    return {"message": "Blog Management API is running. Visit /docs for Swagger UI."}
