# db/repository.py

"""Repository for the database"""

# Standard Imports
from datetime import datetime, timezone
from typing import Optional

# Third Party Imports
from loguru import logger
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

# Local Imports
from core.constants import TriageState
from db.models import Message, Session, TriageResult
from schemas.triage import ExtractedSymptoms, TriageDecision


## Session Management

async def create_session(db: AsyncSession) -> Session:
    """Create a new triage session in IDLE state."""
    session = Session(state=TriageState.IDLE)
    db.add(session)
    await db.flush()
    logger.info("Created new session", session_id=session.id)
    return session


async def get_session(db: AsyncSession, session_id: str) -> Optional[Session]:
    """Retrieve a session by ID. Returns None if not found."""
    result = await db.execute(
        select(Session).where(Session.id == session_id)
    )
    return result.scalar_one_or_none()


async def update_session_state(
    db: AsyncSession,
    session_id: str,
    new_state: TriageState,
) -> None:
    """Update the state of a session."""
    await db.execute(
        update(Session)
        .where(Session.id == session_id)
        .values(state=new_state)
    )
    await db.flush()
    logger.info("Session state updated", session_id=session_id, state=new_state)


async def complete_session(db: AsyncSession, session_id: str) -> None:
    """Mark a session as completed with the current UTC timestamp."""
    await db.execute(
        update(Session)
        .where(Session.id == session_id)
        .values(state=TriageState.COMPLETED, completed_at=datetime.now(timezone.utc))
    )
    await db.flush()
    logger.info("Session completed", session_id=session_id)


## Message Management

async def add_user_message(
    db: AsyncSession,
    session_id: str,
    content: str,
    extracted_symptoms: Optional[ExtractedSymptoms] = None,
) -> Message:
    """Persist a user message with its extracted symptom data."""
    message = Message(
        session_id=session_id,
        role="user",
        content=content,
        extracted_symptoms=extracted_symptoms.model_dump() if extracted_symptoms else None,
    )
    db.add(message)
    await db.flush()
    logger.debug("User message saved", session_id=session_id, message_id=message.id)
    return message


async def add_bot_message(
    db: AsyncSession,
    session_id: str,
    content: str,
    triage_decision: Optional[TriageDecision] = None,
) -> Message:
    """Persist a bot message, optionally with a triage decision."""
    message = Message(
        session_id=session_id,
        role="bot",
        content=content,
        triage_decision=triage_decision.model_dump() if triage_decision else None,
    )
    db.add(message)
    await db.flush()
    logger.debug("Bot message saved", session_id=session_id, message_id=message.id)
    return message


async def get_conversation_history(
    db: AsyncSession,
    session_id: str,
) -> list[Message]:
    """Retrieve all messages for a session, ordered by creation time."""
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at)
    )
    return list(result.scalars().all())


## Triage Result

async def save_triage_result(
    db: AsyncSession,
    session_id: str,
    decision: TriageDecision,
) -> TriageResult:
    """Persist the final triage decision for a session."""
    result_record = TriageResult(
        session_id=session_id,
        urgency=decision.urgency,
        severity=decision.severity,
        department=decision.department,
        recommendation=decision.recommendation,
        disclaimer=decision.disclaimer,
        is_critical_override=decision.is_critical_override,
    )
    db.add(result_record)
    await db.flush()
    logger.info("Triage result saved", session_id=session_id, urgency=decision.urgency)
    return result_record


## History Retrieval

async def get_session_history(
    db: AsyncSession,
    session_id: str,
) -> Optional[Session]:
    """Retrieve a session with all messages and triage result eagerly loaded."""
    result = await db.execute(
        select(Session)
        .where(Session.id == session_id)
        .options(
            selectinload(Session.messages),
            selectinload(Session.triage_result),
        )
    )
    return result.scalar_one_or_none()


async def list_sessions(
    db: AsyncSession,
    limit: int = 50,
    offset: int = 0,
) -> list[Session]:
    """List sessions ordered by creation time (newest first), with pagination."""
    result = await db.execute(
        select(Session)
        .order_by(Session.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())
