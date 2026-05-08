# triage/pipeline.py

"""Triage pipeline orchestrator.

Coordinates: extraction → normalization → rules → decision → persistence.
Single entry point for the API layer.
"""

from datetime import datetime

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from ai.extractor import extract_symptoms, generate_follow_up
from core.constants import (
    TRIAGE_DISCLAIMER,
    URGENCY_RECOMMENDATION_MAP,
    TriageState,
    UrgencyLevel,
)
from db.repository import (
    add_bot_message,
    add_user_message,
    complete_session,
    create_session,
    get_conversation_history,
    get_session,
    save_triage_result,
    update_session_state,
)
from schemas.chat import BotResponse, StartSessionResponse
from schemas.triage import EncounterSummary, ExtractedSymptoms, TriageDecision
from triage.classifier import classify_urgency
from triage.decision import (
    build_missing_info,
    build_symptoms_summary,
    get_all_symptom_names,
    get_chief_complaint,
    get_overall_severity,
    is_sufficient,
)
from triage.normalizer import normalize
from triage.router import route_to_department
from triage.rules import is_emergency_override


# ----- Public API -----


async def start_session(db: AsyncSession) -> StartSessionResponse:
    """Create a new triage session."""
    session = await create_session(db)
    await update_session_state(db, session.id, TriageState.GATHERING)
    logger.info("Session started", session_id=session.id)
    return StartSessionResponse(
        session_id=session.id,
        state=TriageState.GATHERING,
        message=(
            "Hello! I'm here to help assess your symptoms and guide you "
            "to the right care. Please describe what you're experiencing."
        ),
    )


async def process_message(
    db: AsyncSession,
    session_id: str,
    user_message: str,
) -> BotResponse:
    """Process one user message through the full pipeline."""
    session = await get_session(db, session_id)
    if session is None:
        raise ValueError(f"Session not found: {session_id}")
    if session.state == TriageState.COMPLETED:
        raise ValueError(f"Session already completed: {session_id}")

    await update_session_state(db, session_id, TriageState.ANALYZING)

    history = await get_conversation_history(db, session_id)
    turn_count = sum(1 for m in history if m.role == "user") + 1

    logger.info("Processing message", session_id=session_id, turn=turn_count)

    # Extract + normalize
    history_dicts = [{"role": m.role, "content": m.content} for m in history]
    extracted = await extract_symptoms(user_message, history_dicts)
    normalized = normalize(extracted)

    # Safety check
    is_emergency = is_emergency_override(normalized)

    # Persist user message
    await add_user_message(db, session_id, user_message, normalized)

    # Branch
    if is_emergency or is_sufficient(normalized, turn_count):
        return await _complete_triage(db, session_id, normalized, is_emergency, turn_count)

    return await _ask_follow_up(db, session_id, normalized)


# ----- Private -----


async def _ask_follow_up(
    db: AsyncSession,
    session_id: str,
    normalized: EncounterSummary,
) -> BotResponse:
    """Generate and persist a follow-up question."""
    summary = build_symptoms_summary(normalized)
    missing = build_missing_info(normalized)
    question = await generate_follow_up(summary, missing, normalized.negated_symptoms)

    await add_bot_message(db, session_id, question)
    await update_session_state(db, session_id, TriageState.GATHERING)

    return BotResponse(
        session_id=session_id,
        state=TriageState.GATHERING,
        bot_message=question,
        extracted_so_far=normalized,
    )


async def _complete_triage(
    db: AsyncSession,
    session_id: str,
    normalized: ExtractedSymptoms,
    is_override: bool,
    turn_count: int,
) -> BotResponse:
    """Classify, route, persist, and complete the session."""
    urgency = UrgencyLevel.EMERGENCY if is_override else classify_urgency(normalized)
    department, _ = route_to_department(normalized)

    triage = TriageDecision(
        urgency=urgency,
        severity=get_overall_severity(normalized),
        department=department,
        recommendation=URGENCY_RECOMMENDATION_MAP[urgency],
        disclaimer=TRIAGE_DISCLAIMER,
        is_critical_override=is_override,
    )

    encounter = EncounterSummary(
        session_id=session_id,
        chief_complaint=get_chief_complaint(normalized),
        urgency=urgency,
        service_type=department,
        triage_timestamp=datetime.utcnow(),
        extracted_symptoms=get_all_symptom_names(normalized),
        conversation_turns=turn_count,
    )

    await save_triage_result(db, session_id, triage)

    bot_message = f"{triage.recommendation}\n\n{TRIAGE_DISCLAIMER}"
    await add_bot_message(db, session_id, bot_message, triage_decision=triage)
    await complete_session(db, session_id)

    logger.info(
        "Triage completed",
        session_id=session_id,
        urgency=urgency,
        department=department,
        turns=turn_count,
    )

    return BotResponse(
        session_id=session_id,
        state=TriageState.COMPLETED,
        bot_message=bot_message,
        triage=triage,
        encounter_summary=encounter,
        extracted_so_far=None,
    )
