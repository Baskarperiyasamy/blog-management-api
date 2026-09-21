from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
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
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> f4a61c9de3181091724c61d126cb113a3c69516f

    # Every user gets an active subscription from day one - defaults to Basic.
    basic_plan = db.query(models.SubscriptionPlan).filter(models.SubscriptionPlan.name == "basic").first()
    if basic_plan:
        user.plan_id = basic_plan.id

<<<<<<< HEAD
=======
=======
>>>>>>> origin/main
>>>>>>> f4a61c9de3181091724c61d126cb113a3c69516f
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
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}
