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
    UrgencyLevel,
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

    Previously this checked symptom.severity.value in CRITICAL_SEVERITY_MARKERS
    where CRITICAL_SEVERITY_MARKERS = {"severe"} — matching ANY symptom the LLM
    rated as severe, including toothaches and muscle aches. That caused massive
    over-triage to Emergency.

    Now checks: symptom is in SEVERITY_ESCALATES_TO_EMERGENCY AND severity == SEVERE.
    Only clinically appropriate symptoms (chest_pain, shortness_of_breath, headache, etc.)
    escalate to Emergency on severe intensity. A severe toothache stays in Dental.

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

    FIX (Bug E): URGENT_SYMPTOMS was defined in constants.py but never called.
    This function is the missing link. It is called from pipeline.py AFTER the
    emergency check and BEFORE classify_urgency().

    This solves the fracture → ROUTINE misclassification (test case 4):
    - "I broke my arm" → fracture extracted at moderate severity (correct)
    - One moderate symptom → classifier returns ROUTINE (wrong)
    - fracture is in URGENT_SYMPTOMS → this function catches it → URGENT (correct)

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

    Computes the active symptom list once and passes it to both checks.
    Either check returning True means this is an emergency override.

    Returns a tuple of (is_emergency, is_mental_health_crisis) so the pipeline
    can route suicidal ideation to a compassionate response path rather than the
    generic "go to ED immediately" message, which is inappropriate for a distressed patient.

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

    FIX (Bug E): New public function. Called from pipeline.py between the
    emergency check and classify_urgency(). Returns True if any symptom is
    in URGENT_SYMPTOMS, which forces UrgencyLevel.URGENT regardless of what
    the count-based classifier would return.

    Args:
        extracted: Normalized symptoms from the normalizer.

    Returns:
        True if any urgent-override condition is detected.
    """
    active_symptoms = _get_active_symptoms(extracted)

    if not active_symptoms:
        return False

    return check_urgent_symptoms(active_symptoms)
