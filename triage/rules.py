# triage/rules.py

"""Rules for triage"""

# Third Party Imports
from loguru import logger

# Local Imports
from core.constants import (
    CRITICAL_SYMPTOMS,
    SEVERITY_ESCALATES_TO_EMERGENCY,
    URGENT_SYMPTOMS,
    Severity,
)
from schemas.triage import ExtractedSymptoms, Symptom


## Private Helpers

def _get_active_symptoms(extracted: ExtractedSymptoms) -> list[Symptom]:
    """Return all non-negated primary and associated symptoms.

    Negated symptoms are excluded so that a patient who explicitly
    denied a critical symptom does not trigger an emergency override.
    """
    negated = set(extracted.negated_symptoms)
    return [
        s for s in extracted.primary_symptoms + extracted.associated_symptoms
        if s.name not in negated
    ]


## Public API

def check_critical_symptoms(symptoms: list[Symptom]) -> bool:
    """Check if any symptom name matches the critical symptoms list.

    This is the hard safety override: if a critical symptom is detected,
    the triage MUST be Emergency regardless of any other logic.

    Args:
        symptoms: Active (non-negated) symptoms from _get_active_symptoms.

    Returns:
        True if any symptom name is in CRITICAL_SYMPTOMS.
    """
    for symptom in symptoms:
        if symptom.name in CRITICAL_SYMPTOMS:
            logger.warning(
                "Critical symptom detected, forcing Emergency",
                symptom=symptom.name,
                severity=symptom.severity,
            )
            return True

    return False


def check_critical_severity(symptoms: list[Symptom]) -> bool:
    """Check if a high-acuity symptom is reported at severe intensity.

    Args:
        symptoms: Active (non-negated) symptoms from _get_active_symptoms.

    Returns:
        True if a scoped high-acuity symptom is present at severe intensity.
    """
    for symptom in symptoms:
        if (
            symptom.name in SEVERITY_ESCALATES_TO_EMERGENCY
            and symptom.severity == Severity.SEVERE
        ):
            logger.warning(
                "Critical severity detected on high-acuity symptom — forcing Emergency",
                symptom=symptom.name,
                severity=symptom.severity,
            )
            return True

    return False


def check_urgent_symptoms(symptoms: list[Symptom]) -> bool:
    """Check if any symptom name matches the urgent symptoms list.

    Args:
        symptoms: Active (non-negated) symptoms from _get_active_symptoms.

    Returns:
        True if any symptom name is in URGENT_SYMPTOMS.
    """
    for symptom in symptoms:
        if symptom.name in URGENT_SYMPTOMS:
            logger.info(
                "Urgent symptom detected, forcing Urgent",
                symptom=symptom.name,
                severity=symptom.severity,
            )
            return True

    return False


def is_emergency_override(extracted: ExtractedSymptoms) -> tuple[bool, bool]:
    """Combined check: should this case be forced to Emergency?

    Args:
        extracted: Normalized symptoms from the normalizer.

    Returns:
        Tuple of (is_emergency: bool, is_mental_health_crisis: bool).
    """
    active_symptoms = _get_active_symptoms(extracted)

    if not active_symptoms:
        logger.debug("No active symptoms for critical check")
        return False, False

    is_mental_health_crisis = any(
        s.name in ("suicidal_ideation", "self_harm") for s in active_symptoms
    )

    if check_critical_symptoms(active_symptoms):
        return True, is_mental_health_crisis

    if check_critical_severity(active_symptoms):
        return True, False

    logger.debug("No critical conditions detected")
    return False, False


def is_urgent_override(extracted: ExtractedSymptoms) -> bool:
    """Check if this case should be forced to Urgent (but not Emergency).

    Args:
        extracted: Normalized symptoms from the normalizer.

    Returns:
        True if any urgent-override condition is detected.
    """
    active_symptoms = _get_active_symptoms(extracted)

    if not active_symptoms:
        return False

    return check_urgent_symptoms(active_symptoms)
