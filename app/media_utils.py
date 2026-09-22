import os
import uuid

from fastapi import HTTPException, UploadFile

MEDIA_ROOT = "media"
POSTS_SUBDIR = "posts"
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


def ensure_media_dirs() -> None:
    os.makedirs(os.path.join(MEDIA_ROOT, POSTS_SUBDIR), exist_ok=True)


def save_post_image(file: UploadFile) -> str:
    """
    Validates and saves an uploaded image under media/posts/.
    Returns the relative path (e.g. "posts/<uuid>.jpg") to store in the DB.
    """
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported image type. Allowed: jpeg, png, webp, gif.",
        )

    ext = os.path.splitext(file.filename or "")[1].lower() or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    relative_path = os.path.join(POSTS_SUBDIR, filename)
    full_path = os.path.join(MEDIA_ROOT, relative_path)

    ensure_media_dirs()

    contents = file.file.read()
    if len(contents) > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="Image must be 5MB or smaller.")

    with open(full_path, "wb") as out:
        out.write(contents)

    return relative_path.replace("\\", "/")  # normalize for Windows paths


def delete_post_image(relative_path: str) -> None:
    if not relative_path:
        return
    full_path = os.path.join(MEDIA_ROOT, relative_path)
    if os.path.exists(full_path):
        try:
            os.remove(full_path)
        except OSError:
            pass


def image_url_for(relative_path: str | None) -> str | None:
    if not relative_path:
        return None
    return f"/media/{relative_path}"
