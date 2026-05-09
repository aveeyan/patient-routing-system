# app/api/routes/triage.py

"""Triage API routes."""

# Standard Imports
from typing import Annotated

# Third Party Imports
from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

# Local Imports
from ai.client import LLMError
from db.repository import get_session, get_session_history, list_sessions
from db.session import get_db
from schemas.chat import (
    BotResponse,
    MessageRequest,
    MessageTurn,
    SessionHistoryResponse,
    SessionListItem,
    SessionListResponse,
    StartSessionResponse,
)
from schemas.triage import TriageDecision
from triage import pipeline

router = APIRouter()


## Route Handlers

@router.post("/start", response_model=StartSessionResponse)
async def start_session(db: AsyncSession = Depends(get_db)):
    """Create a new triage session."""
    return await pipeline.start_session(db)


@router.post("/message", response_model=BotResponse)
async def send_message(
    request: MessageRequest,
    db: AsyncSession = Depends(get_db),
):
    """Send a message to the triage chatbot."""
    session = await get_session(db, request.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        return await pipeline.process_message(db, request.session_id, request.message)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except LLMError as e:
        logger.error("LLM unavailable during message processing", error=str(e))
        raise HTTPException(
            status_code=503,
            detail="AI service temporarily unavailable. Please try again shortly.",
        )


@router.get("/history/{session_id}", response_model=SessionHistoryResponse)
async def get_history(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve the full history of a triage session."""
    session = await get_session_history(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    triage: TriageDecision | None = None
    if session.triage_result:
        triage = TriageDecision.model_validate(
            session.triage_result.__dict__,
            from_attributes=True,
        )

    return SessionHistoryResponse(
        session_id=session.id,
        state=session.state,
        messages=[
            MessageTurn(
                role=msg.role,
                content=msg.content,
                timestamp=msg.created_at,
            )
            for msg in session.messages
        ],
        triage=triage,
        created_at=session.created_at,
        completed_at=session.completed_at,
    )


@router.get("/sessions", response_model=SessionListResponse)
async def list_all_sessions(
    db: AsyncSession = Depends(get_db),
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """List triage sessions with pagination.

    Args:
        limit: Maximum number of sessions to return (1-100, default 50).
        offset: Number of sessions to skip for pagination (default 0).
    """
    sessions = await list_sessions(db, limit=limit, offset=offset)

    return SessionListResponse(
        sessions=[
            SessionListItem(
                session_id=s.id,
                state=s.state,
                created_at=s.created_at,
                summary=s.messages[0].content[:200] if s.messages else None,
            )
            for s in sessions
        ],
    )
