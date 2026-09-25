"""
routers/ai_support.py — the AI Support Chat feature: users send a message
and get an instant reply, either from the mocked FAQ knowledge base or a
real OpenAI call if OPENAI_API_KEY is configured (see services/ai_support_service.py).

The endpoint works for both logged-in and anonymous visitors (so the chat
widget can sit on any page, public or private), but logs the user_id when
one is available.
"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user_optional
from ..services.ai_support_service import get_ai_reply

router = APIRouter(prefix="/api/ai-support", tags=["AI Support Chat"])


@router.post("/", response_model=schemas.ChatResponse)
def chat(
    chat_in: schemas.ChatRequest,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user_optional),
):
    """
    Accepts a user message, returns an AI-generated (or FAQ-matched) reply,
    and logs the exchange to chat_logs. Works whether or not the caller is
    logged in - pass a bearer token to have the chat tied to your account,
    or call it anonymously.
    """
    reply, matched_topic, source = get_ai_reply(chat_in.message)

    log_entry = models.ChatLog(
        user_id=current_user.id if current_user else None,
        question=chat_in.message,
        ai_response=reply,
        matched_topic=matched_topic,
    )
    db.add(log_entry)
    db.commit()

    return schemas.ChatResponse(reply=reply, matched_topic=matched_topic, source=source)


@router.get("/history", response_model=list[schemas.ChatHistoryItem])
def chat_history(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user_optional),
):
    """
    Returns the caller's own past chat exchanges, most recent first.
    Requires a valid token (anonymous chats aren't tied to anyone, so
    there's nothing to look up without one).
    """
    if not current_user:
        return []

    logs = (
        db.query(models.ChatLog)
        .filter(models.ChatLog.user_id == current_user.id)
        .order_by(models.ChatLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return logs
