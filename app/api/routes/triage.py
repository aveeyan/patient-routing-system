# app/api/routes/triage.py (corrected)

"""Triage API routes."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db.repository import get_session_history, list_sessions
from db.session import get_db
from schemas.chat import (
    BotResponse,
    MessageRequest,
    MessageTurn,
    SessionHistoryResponse,
    SessionListResponse,
    SessionListItem,
    StartSessionResponse,
)
from schemas.triage import TriageDecision
from triage import pipeline

router = APIRouter()


@router.post("/start", response_model=StartSessionResponse)
async def start_session(db: AsyncSession = Depends(get_db)):
    """Create a new triage session."""
    return await pipeline.start_session(db)


@router.post("/message", response_model=BotResponse)
async def send_message(request: MessageRequest, db: AsyncSession = Depends(get_db)):
    """Send a message to the triage chatbot."""
    try:
        return await pipeline.process_message(db, request.session_id, request.message)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history/{session_id}", response_model=SessionHistoryResponse)
async def get_history(session_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve the full history of a triage session."""
    session = await get_session_history(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    triage = None
    if session.triage_result:
        triage = TriageDecision(
            urgency=session.triage_result.urgency,
            severity=session.triage_result.severity,
            department=session.triage_result.department,
            recommendation=session.triage_result.recommendation,
            disclaimer=session.triage_result.disclaimer,
            is_critical_override=session.triage_result.is_critical_override,
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
async def list_all_sessions(db: AsyncSession = Depends(get_db)):
    """List all triage sessions."""
    sessions = await list_sessions(db)
    return SessionListResponse(
        sessions=[
            SessionListItem(
                session_id=s.id,
                state=s.state,
                created_at=s.created_at,
                summary=s.messages[0].content[:100] if s.messages else None,
            )
            for s in sessions
        ],
        total=len(sessions),
    )
