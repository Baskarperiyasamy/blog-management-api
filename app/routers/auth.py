from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
<<<<<<< HEAD
from ..deps import get_current_user
=======
>>>>>>> 4bc8c0b2a9d01a4b783a740424ee0c3addbb7294
from ..security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED
)
def register(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new user. Passwords are hashed before being stored."""
    existing = (
        db.query(models.User)
        .filter(
            (models.User.username == user_in.username)
            | (models.User.email == user_in.email)
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered",
        )

    user = models.User(
        username=user_in.username,
        email=user_in.email,
        password=hash_password(user_in.password),
    )

    # Every user gets an active subscription from day one - defaults to Basic.
    basic_plan = db.query(models.SubscriptionPlan).filter(models.SubscriptionPlan.name == "basic").first()
    if basic_plan:
        user.plan_id = basic_plan.id

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=schemas.Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """
    Log in with username + password (OAuth2 password flow) and receive a JWT.

    NOTE: In Swagger UI, click the green "Authorize" button and enter your
    username/password there - it calls this exact endpoint and stores the
    token for you automatically for all subsequent requests.
    """
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
<<<<<<< HEAD

    if user and not user.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"This account signed up with {user.auth_provider.title()}. "
                   f"Please use 'Continue with {user.auth_provider.title()}' instead of a password.",
        )

=======
>>>>>>> 4bc8c0b2a9d01a4b783a740424ee0c3addbb7294
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}
<<<<<<< HEAD


@router.get("/me", response_model=schemas.UserOut)
def get_me(current_user: models.User = Depends(get_current_user)):
    """Returns the currently authenticated user's own profile - used by the
    login page (and any other page) to check who's signed in from just the
    saved JWT, without decoding it client-side."""
    return current_user
=======
>>>>>>> 4bc8c0b2a9d01a4b783a740424ee0c3addbb7294
