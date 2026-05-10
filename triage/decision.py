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

    Args:
        extracted: Normalized symptoms from the normalizer.
        turn_count: Number of user messages received so far (1-indexed).

    Returns:
        True if the pipeline should proceed to triage, False to ask a follow-up.
    """
    if turn_count >= settings.max_conversation_turns:
        return True

    if turn_count <= 2:
        return False

    all_symptoms = extracted.primary_symptoms + extracted.associated_symptoms
    total_symptoms = len(all_symptoms)
    has_duration = any(s.duration for s in all_symptoms)
    has_body_site = any(s.body_site for s in all_symptoms)
    min_symptoms = settings.min_data_points  # default: 3

    if turn_count == 3:
        if has_duration and total_symptoms >= min_symptoms:
            return True
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
    """
    Human-readable summary of what we've extracted so far.
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

    Keep each item short: the LLM's warmth and phrasing come entirely from the FOLLOW_UP_PROMPT instructions, not from this string.
    """
    missing = []
    all_symptoms = extracted.primary_symptoms + extracted.associated_symptoms

    if not any(s.duration for s in all_symptoms):
        missing.append("duration not captured")

    if not any(s.body_site for s in all_symptoms) and len(all_symptoms) == 1:
        missing.append(f"body site for {all_symptoms[0].name.replace('_', ' ')}")

    if len(all_symptoms) == 1 and all_symptoms[0].severity == Severity.MODERATE:
        missing.append("severity clarification")

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
