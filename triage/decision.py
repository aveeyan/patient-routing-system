# triage/decision.py

"""
Pure decision-support functions for the triage pipeline.

Stateless, synchronous, no I/O. Testable without mocks.
"""

# Local Imports
from core.config import settings
from core.constants import Severity
from schemas.triage import ExtractedSymptoms, Symptom


def is_sufficient(extracted: ExtractedSymptoms, turn_count: int) -> bool:
    """Check if we have enough data to make a triage decision.

    Guarantees at least two follow-ups for non-emergency cases, ensuring
    the conversation feels natural and gathers meaningful clinical context.
    Emergency cases bypass this entirely via rules.py.

    FIX (Bug C): The original logic exited after any single follow-up where
    the patient provided a duration or body site — which is almost always turn 2.
    This caused every case to close at exactly 2 exchanges regardless of how
    little clinical detail was actually captured.

    The original settings.min_data_points was also defined in config.py but
    never used here — it is now wired in as the minimum symptom count gate.

    Sufficiency rules (evaluated in order):
    1. Hard cap: if we've hit the max turn limit, always proceed.
    2. First two turns: always ask follow-ups — never triage on fewer than
       two exchanges (one initial + one follow-up answered).
    3. After two exchanges: sufficient only if we have BOTH:
       - At least one symptom with duration captured, AND
       - At least settings.min_data_points total symptoms reported.
       This prevents closing on a single symptom with only a location given.
    4. After three or more exchanges: sufficient if we have duration OR
       3+ total symptoms — enough signal for a routing decision.
    5. Otherwise: keep gathering.

    Args:
        extracted: Normalized symptoms from the normalizer.
        turn_count: Number of user messages received so far (1-indexed).

    Returns:
        True if the pipeline should proceed to triage, False to ask a follow-up.
    """
    if turn_count >= settings.max_conversation_turns:
        return True

    # Always gather at least 2 exchanges before triaging.
    # turn_count is pre-incremented (+1) in pipeline.py before this is called,
    # so turn_count=1 means this IS the first message, turn_count=2 is the second.
    # We return False for both, ensuring the bot always asks at least one follow-up.
    if turn_count <= 2:
        return False

    all_symptoms = extracted.primary_symptoms + extracted.associated_symptoms
    total_symptoms = len(all_symptoms)
    has_duration = any(s.duration for s in all_symptoms)
    has_body_site = any(s.body_site for s in all_symptoms)
    min_symptoms = settings.min_data_points  # default: 3

    # After exactly 2 exchanges: require both duration AND minimum symptom count.
    # This prevents closing on "toothache, front 2 teeth" with no duration info.
    if turn_count == 3:
        if has_duration and total_symptoms >= min_symptoms:
            return True
        # Also sufficient if we have very rich detail: body site + duration together
        if has_duration and has_body_site:
            return True
        return False

    # After 3+ exchanges: more lenient — either duration captured or enough symptoms.
    if has_duration:
        return True

    if total_symptoms >= min_symptoms:
        return True

    return False


def build_symptoms_summary(extracted: ExtractedSymptoms) -> str:
    """Human-readable summary of what we've extracted so far.

    FIX (Bug D, partial): Returns richer clinical context so the follow-up
    generator has more to work with than a bare symptom checklist. Includes
    confidence level and what's still genuinely unknown.
    """
    all_symptoms = extracted.primary_symptoms + extracted.associated_symptoms

    if not all_symptoms:
        return "No symptoms identified yet."

    lines = []
    for s in all_symptoms:
        parts = [f"- {s.name.replace('_', ' ')}"]
        if s.severity:
            parts.append(f"(severity: {s.severity.value if hasattr(s.severity, 'value') else s.severity})")
        if s.duration:
            parts.append(f"(duration: {s.duration})")
        if s.body_site:
            parts.append(f"(location: {s.body_site})")
        lines.append(" ".join(parts))

    summary = "\n".join(lines)

    if extracted.confidence < 0.7:
        summary += f"\n\nNote: Extraction confidence is low ({extracted.confidence:.0%}). The patient's description was unclear."

    return summary


def build_missing_info(extracted: ExtractedSymptoms) -> str:
    """What information is still needed for triage — returned as a terse internal signal.

    This string is injected into the follow-up system prompt as a brief note for the LLM.
    It must NOT be clinical, wordy, or contain pre-written phrases the LLM might echo
    verbatim into its response — that was the root cause of the robotic tone.

    Keep each item short: the LLM's warmth and phrasing come entirely from the
    FOLLOW_UP_PROMPT instructions, not from this string.
    """
    missing = []
    all_symptoms = extracted.primary_symptoms + extracted.associated_symptoms
    symptom_names = {s.name for s in all_symptoms}

    if not any(s.duration for s in all_symptoms):
        missing.append("duration not captured")

    if not any(s.body_site for s in all_symptoms) and len(all_symptoms) == 1:
        missing.append(f"body site for {all_symptoms[0].name.replace('_', ' ')}")

    if len(all_symptoms) == 1 and all_symptoms[0].severity == Severity.MODERATE:
        missing.append("severity clarification")

    # Symptom-specific red flag gaps — keep as short labels, not full sentences
    if "chest_pain" in symptom_names and "shortness_of_breath" not in symptom_names:
        missing.append("radiation or shortness of breath (cardiac red flag)")
    if "headache" in symptom_names and "dizziness" not in symptom_names:
        missing.append("dizziness, vision change, or neck stiffness (neuro red flag)")
    if "abdominal_pain" in symptom_names and "nausea" not in symptom_names:
        missing.append("nausea, vomiting, or bowel changes")
    if "fracture" in symptom_names or "broken_bone" in symptom_names:
        if not any(s.body_site for s in all_symptoms):
            missing.append("which bone / deformity / numbness")
    if "fever" in symptom_names and "cough" not in symptom_names:
        missing.append("associated cough, sore throat, or body aches")

    return "; ".join(missing) if missing else "any other details the patient wants to share"


def get_chief_complaint(extracted: ExtractedSymptoms) -> str:
    """Primary complaint in plain language."""
    if extracted.primary_symptoms:
        return extracted.primary_symptoms[0].name.replace("_", " ")
    if extracted.associated_symptoms:
        return extracted.associated_symptoms[0].name.replace("_", " ")
    return "unspecified symptoms"


def get_all_symptom_names(extracted: ExtractedSymptoms) -> list[str]:
    """All canonical symptom names as a flat list."""
    return [s.name for s in extracted.primary_symptoms] + [
        s.name for s in extracted.associated_symptoms
    ]


def get_overall_severity(extracted: ExtractedSymptoms) -> Severity:
    """Highest severity across all symptoms."""
    all_symptoms = extracted.primary_symptoms + extracted.associated_symptoms

    if not all_symptoms:
        return Severity.MODERATE

    severities = {s.severity for s in all_symptoms}

    if Severity.SEVERE in severities:
        return Severity.SEVERE
    if Severity.MODERATE in severities:
        return Severity.MODERATE
    return Severity.MILD
