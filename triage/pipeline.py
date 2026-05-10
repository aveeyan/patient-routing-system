# triage/pipeline.py

"""Triage pipeline orchestrator.

Coordinates: extraction → normalization → rules → decision → persistence.
Single entry point for the API layer.
"""

from datetime import datetime, timezone

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from ai.extractor import extract_symptoms, generate_follow_up
from core.constants import (
    TRIAGE_DISCLAIMER,
    URGENCY_RECOMMENDATION_MAP,
    Department,
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
from triage.rules import is_emergency_override, is_urgent_override


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
            "Hello! I'm Samira, and I'm here to help make sure you get the right care today. "
            "Please tell me what's been bothering you, and I'll ask a couple of questions "
            "to point you in the right direction."
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

    # Safety check — emergency first.
    # is_emergency_override now returns (is_emergency, is_mental_health_crisis).
    # The second flag routes suicidal ideation to a compassionate message
    # instead of the generic "go to ED immediately" response.
    is_emergency, is_mental_health_crisis = is_emergency_override(normalized)

    # Check urgent override BEFORE the classifier.
    is_urgent = False
    if not is_emergency:
        is_urgent = is_urgent_override(normalized)

    # Persist user message
    await add_user_message(db, session_id, user_message, normalized)

    # Branch: emergency always skips further questions.
    # Urgent/routine: check if we have enough data before deciding.
    if is_emergency or is_sufficient(normalized, turn_count):
        return await _complete_triage(
            db, session_id, normalized, is_emergency, is_urgent,
            is_mental_health_crisis, turn_count
        )

    # FIX (Bug A): Pass history_dicts to _ask_follow_up so it can be forwarded
    # to generate_follow_up(). Without this, the bot had no memory of what it
    # already asked, causing repeated and robotic questions.
    return await _ask_follow_up(db, session_id, normalized, history_dicts)


# ----- Private -----


async def _ask_follow_up(
    db: AsyncSession,
    session_id: str,
    normalized: ExtractedSymptoms,
    conversation_history: list[dict[str, str]],
) -> BotResponse:
    """Generate and persist a follow-up question.

    FIX (Bug A): conversation_history is now accepted and passed to
    generate_follow_up(), which injects it into the FOLLOW_UP_PROMPT so
    the LLM knows what has already been said and does not repeat itself.
    """
    summary = build_symptoms_summary(normalized)
    missing = build_missing_info(normalized)

    # FIX (Bug A): Pass history so the LLM can see the full conversation.
    question = await generate_follow_up(
        symptoms_summary=summary,
        missing_info=missing,
        negated_symptoms=normalized.negated_symptoms,
        conversation_history=conversation_history,
    )

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
    is_urgent: bool,
    is_mental_health_crisis: bool,
    turn_count: int,
) -> BotResponse:
    """Classify, route, persist, and complete the session."""
    if is_override:
        urgency = UrgencyLevel.EMERGENCY
    elif is_urgent:
        urgency = UrgencyLevel.URGENT
        logger.info("Urgent override applied — skipping classifier", session_id=session_id)
    else:
        urgency = classify_urgency(normalized)

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
        severity=get_overall_severity(normalized),
        service_type=department,
        triage_timestamp=datetime.now(timezone.utc),  # fixed: was datetime.utcnow() (deprecated)
        extracted_symptoms=get_all_symptom_names(normalized),
        conversation_turns=turn_count,
    )

    await save_triage_result(db, session_id, triage)

    bot_message = _build_triage_message(triage, department, normalized, is_mental_health_crisis)
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


def _build_triage_message(
    triage: "TriageDecision",
    department: "Department",
    normalized: ExtractedSymptoms,
    is_mental_health_crisis: bool = False,
) -> str:
    """Build a plain-text conversational triage result for the chat bubble."""
    department_name = department.value.replace("_", " ").title()
    urgency = triage.urgency
    complaint = (
        normalized.primary_symptoms[0].name.replace("_", " ")
        if normalized.primary_symptoms
        else "your symptoms"
    )

    # ── Mental health crisis ───────────────────────────────────────────────
    # Suicidal ideation and active self-harm must never receive the generic
    # "go to ED immediately" message — a distressed patient needs warmth first.
    if is_mental_health_crisis:
        return (
            "I'm really glad you reached out, and I want you to know you're not alone. "
            "What you're going through sounds very difficult. "
            "Please reach out to a mental health professional or a crisis line right away — "
            "they are there to help, and you deserve support. "
            "If you feel you are in immediate danger, please go to the Emergency Department "
            "or call emergency services. You don't have to face this alone."
        )

    # ── Emergency ──────────────────────────────────────────────────────────
    if urgency == UrgencyLevel.EMERGENCY:
        if department not in (Department.EMERGENCY, Department.OPD, Department.GENERAL_MEDICINE):
            dept_note = (
                f"When you arrive, let the desk know you are here for {complaint} "
                f"— they will contact the {department_name} team on call."
            )
        else:
            dept_note = "Let the front desk know you are here urgently."

        return (
            f"Based on what you've described — {complaint} — this needs immediate attention. "
            f"Please go to the Emergency Department right away, "
            f"or call emergency services if you cannot travel safely. "
            f"{dept_note}"
        )

    # ── OPD / General Medicine ─────────────────────────────────────────────
    if department in (Department.OPD, Department.GENERAL_MEDICINE):
        if urgency == UrgencyLevel.URGENT:
            return (
                f"Based on your symptoms, I'd recommend you be seen today. "
                f"Please head to the OPD registration desk and let them know you need "
                f"a same-day appointment. Try not to delay this visit."
            )
        return (
            f"Based on what you've shared, a routine OPD visit should be appropriate. "
            f"You can register at the OPD desk and schedule an appointment at your convenience. "
            f"If your symptoms worsen before then, please come in sooner."
        )

    # ── Specialist departments ─────────────────────────────────────────────
    if urgency == UrgencyLevel.URGENT:
        return (
            f"Thank you for sharing that. Based on your symptoms, you should be seen today "
            f"by the {department_name} team. "
            f"Please go to the OPD registration desk and ask for a same-day referral to {department_name}. "
            f"If your symptoms get significantly worse while waiting, let the staff know immediately."
        )

    return (
        f"I've noted your symptoms. A visit to the {department_name} department looks appropriate. "
        f"\nPlease go to the OPD desk and ask them to book you an appointment with {department_name}. "
        f"You can schedule this at a time that works for you."
    )
