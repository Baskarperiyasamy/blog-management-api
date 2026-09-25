from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from . import models
from .database import get_db
from .security import decode_access_token

# tokenUrl points Swagger UI's "Authorize" button at our login endpoint.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_access_token(token)
    if payload is None:
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception

    return user


# Optional variant: does not require the request to be authenticated. Used by
# endpoints (like AI Support Chat) that should work for anonymous visitors,
# but still identify the caller when a valid token is provided.
_optional_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)


def get_current_user_optional(
    token: str | None = Depends(_optional_oauth2_scheme), db: Session = Depends(get_db)
) -> models.User | None:
    if not token:
        return None
    payload = decode_access_token(token)
    if payload is None:
        return None
    user_id = payload.get("sub")
    if user_id is None:
        return None
    return db.query(models.User).filter(models.User.id == int(user_id)).first()
