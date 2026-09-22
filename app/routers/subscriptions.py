from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user
from ..invoice_utils import generate_invoice_pdf, generate_transaction_id
from ..media_utils import image_url_for
from ..plan_limits import get_active_plan

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions"])

VALID_PLAN_NAMES = {"basic", "premium", "pro"}


@router.get("/plans", response_model=List[schemas.SubscriptionPlanOut])
def list_plans(db: Session = Depends(get_db)):
    """Public endpoint - the 3 fixed plans (basic / premium / pro) and their limits."""
    return db.query(models.SubscriptionPlan).order_by(models.SubscriptionPlan.price).all()


@router.post("/subscribe", response_model=schemas.BillingHistoryOut, status_code=status.HTTP_201_CREATED)
def subscribe(
    payload: schemas.SubscribeRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Subscribe (or switch/renew) to a plan. Generates a BillingHistory row
    plus a fake invoice PDF (ReportLab), and makes this the user's active
    plan going forward.
    """
    plan_name = payload.plan_name.strip().lower()
    if plan_name not in VALID_PLAN_NAMES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid plan_name. Must be one of: {', '.join(sorted(VALID_PLAN_NAMES))}",
        )

    plan = db.query(models.SubscriptionPlan).filter(models.SubscriptionPlan.name == plan_name).first()
    if not plan:
        raise HTTPException(status_code=500, detail="Plan not found - has the DB been seeded?")

    start_date = datetime.utcnow()
    end_date = start_date + timedelta(days=plan.duration_days)
    transaction_id = generate_transaction_id()

    invoice_relative_path = generate_invoice_pdf(
        user_name=current_user.username,
        plan_name=plan.name,
        price=plan.price,
        start_date=start_date,
        end_date=end_date,
        transaction_id=transaction_id,
    )

    billing = models.BillingHistory(
        user_id=current_user.id,
        plan_id=plan.id,
        transaction_id=transaction_id,
        amount=plan.price,
        start_date=start_date,
        end_date=end_date,
        invoice_path=invoice_relative_path,
    )
    db.add(billing)

    # This becomes the user's new active plan.
    current_user.plan_id = plan.id

    db.commit()
    db.refresh(billing)

    return schemas.BillingHistoryOut(
        id=billing.id,
        plan_id=billing.plan_id,
        plan_name=plan.name,
        transaction_id=billing.transaction_id,
        amount=billing.amount,
        start_date=billing.start_date,
        end_date=billing.end_date,
        invoice_url=image_url_for(billing.invoice_path),
        created_at=billing.created_at,
    )


@router.get("/mine", response_model=schemas.MyPlanOut)
def my_plan(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Current user's active plan plus how much of each limit they've used so far."""
    plan = get_active_plan(db, current_user)

    posts_used = db.query(models.Post).filter(models.Post.author_id == current_user.id).count()
    images_used = (
        db.query(models.Post)
        .filter(models.Post.author_id == current_user.id, models.Post.image.isnot(None))
        .count()
    )
    likes_used = db.query(models.Like).filter(models.Like.user_id == current_user.id).count()
    comments_used = db.query(models.Comment).filter(models.Comment.user_id == current_user.id).count()

    return schemas.MyPlanOut(
        plan=schemas.SubscriptionPlanOut.model_validate(plan),
        usage=schemas.MyPlanUsage(
            posts_used=posts_used,
            posts_limit=plan.max_posts,
            images_used=images_used,
            images_limit=plan.max_images_per_post,
            likes_used=likes_used,
            likes_limit=plan.max_likes,
            comments_used=comments_used,
            comments_limit=plan.max_comments,
        ),
    )


@router.get("/billing-history", response_model=List[schemas.BillingHistoryOut])
def billing_history(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """All of the current user's past subscriptions/renewals, each with its invoice link."""
    rows = (
        db.query(models.BillingHistory)
        .filter(models.BillingHistory.user_id == current_user.id)
        .order_by(models.BillingHistory.created_at.desc())
        .all()
    )
    return [
        schemas.BillingHistoryOut(
            id=b.id,
            plan_id=b.plan_id,
            plan_name=b.plan.name if b.plan else None,
            transaction_id=b.transaction_id,
            amount=b.amount,
            start_date=b.start_date,
            end_date=b.end_date,
            invoice_url=image_url_for(b.invoice_path),
            created_at=b.created_at,
        )
        for b in rows
    ]
