# triage/rules.py

"""Rules for triage"""

# Third Party Imports
from loguru import logger

# Local Imports
from core.constants import CRITICAL_SEVERITY_MARKERS, CRITICAL_SYMPTOMS, Severity
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

    This is the safety override: if a critical symptom is detected,
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
    """Check if any symptom carries a severity marker that escalates to Emergency.

    Compares symptom severity against CRITICAL_SEVERITY_MARKERS using the
    string value of the Severity enum to avoid type mismatch. Markers in
    CRITICAL_SEVERITY_MARKERS that are not valid Severity enum values (such
    as "unbearable" or "life_threatening") are compared against the raw
    symptom name as a fallback, since they may appear as symptom descriptors
    rather than severity levels.

    Args:
        symptoms: Active (non-negated) symptoms from _get_active_symptoms.

    Returns:
        True if any symptom severity value is in CRITICAL_SEVERITY_MARKERS.
    """
    for symptom in symptoms:
        if symptom.severity.value in CRITICAL_SEVERITY_MARKERS:
            logger.warning(
                "Critical severity marker detected, forcing Emergency",
                symptom=symptom.name,
                severity=symptom.severity,
            )
            return True

    return False


def is_emergency_override(extracted: ExtractedSymptoms) -> bool:
    """Combined check: should this case be forced to Emergency?

    Computes the active symptom list once and passes it to both checks.
    Either check returning True means this is an emergency override.

    Args:
        extracted: Normalized symptoms from the normalizer.

    Returns:
        True if any critical condition is detected.
    """
    active_symptoms = _get_active_symptoms(extracted)

    if not active_symptoms:
        logger.debug("No active symptoms for critical check")
        return False

    if check_critical_symptoms(active_symptoms):
        return True

    if check_critical_severity(active_symptoms):
        return True

    logger.debug("No critical conditions detected")
    return False
