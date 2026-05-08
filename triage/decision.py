# triage/decision.py

"""
Pure decision-support functions for the triage pipeline.

Stateless, synchronous, no I/O. Testable without mocks.
"""

# Local Imports
from core.config import settings
from core.constants import Severity
from schemas.triage import ExtractedSymptoms


def is_sufficient(extracted: ExtractedSymptoms, turn_count: int) -> bool:
    """Check if we have enough data to make a triage decision."""
    if turn_count >= settings.max_conversation_turns:
        return True

    all_symptoms = extracted.primary_symptoms + extracted.associated_symptoms
    points = len(all_symptoms)

    if any(s.duration for s in all_symptoms):
        points += 1
    if any(s.body_site for s in all_symptoms):
        points += 1
    if extracted.confidence >= 0.8:
        points += 1

    return points >= settings.confidence_threshold


def build_symptoms_summary(extracted: ExtractedSymptoms) -> str:
    """Human-readable summary of what we've extracted so far."""
    all_symptoms = extracted.primary_symptoms + extracted.associated_symptoms

    if not all_symptoms:
        return "No symptoms identified yet."

    lines = []
    for s in all_symptoms:
        parts = [f"- {s.name.replace('_', ' ')}"]
        if s.severity:
            parts.append(f"(severity: {s.severity})")
        if s.duration:
            parts.append(f"(duration: {s.duration})")
        if s.body_site:
            parts.append(f"(location: {s.body_site})")
        lines.append(" ".join(parts))

    return "\n".join(lines)


def build_missing_info(extracted: ExtractedSymptoms) -> str:
    """What information is still needed for triage."""
    missing = []
    all_symptoms = extracted.primary_symptoms + extracted.associated_symptoms

    if not any(s.duration for s in all_symptoms):
        missing.append("when the symptoms started and how long they have lasted")

    if not any(s.body_site for s in all_symptoms) and len(all_symptoms) == 1:
        name = all_symptoms[0].name.replace("_", " ")
        missing.append(f"the exact location of the {name}")

    if all(s.severity == "moderate" for s in all_symptoms) and len(all_symptoms) == 1:
        missing.append("how severe the symptom is (mild, moderate, or severe)")

    primary_names = {s.name for s in all_symptoms}

    if "chest_pain" in primary_names and "shortness_of_breath" not in primary_names:
        missing.append("whether there is any shortness of breath")
    if "headache" in primary_names and "dizziness" not in primary_names:
        missing.append("whether there is any dizziness or vision changes")
    if "abdominal_pain" in primary_names and "nausea" not in primary_names:
        missing.append("whether there is any nausea or vomiting")

    return "; ".join(missing) if missing else "any other symptoms or relevant details"


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
