# triage/classifier.py

"""Classifier of Triage"""

# Third Party Imports
from loguru import logger

# Local Imports
from core.constants import Severity, UrgencyLevel
from schemas.triage import ExtractedSymptoms


## Classification Thresholds
#
# These constants define the *minimum count* at which a condition escalates to URGENT.
# Naming convention: _MIN_<SEVERITY>_FOR_URGENT means "at least this many of that severity → URGENT".
#
# FIX: The original constants were named "THRESHOLD" but used with >=, implying they are
# inclusive lower bounds. Renamed to make the semantics unambiguous, preventing future
# off-by-one errors when these values are adjusted.

# Any single severe symptom triggers URGENT.
_MIN_SEVERE_FOR_URGENT = 1

# Two or more moderate symptoms trigger URGENT.
_MIN_MODERATE_FOR_URGENT = 2

# One moderate symptom among three or more total symptoms triggers URGENT.
# (The moderate symptom + context of multiple complaints is a meaningful signal.)
_MIN_TOTAL_WITH_MODERATE_FOR_URGENT = 3

# Extraction confidence below this value triggers URGENT (erring on side of caution).
_LOW_CONFIDENCE_THRESHOLD = 0.5


## Public API

def classify_urgency(extracted: ExtractedSymptoms) -> UrgencyLevel:
    """Classify the urgency level based on extracted symptoms.

    This is the decision engine for non-critical cases.
    Critical overrides are handled by rules.py BEFORE this is called.

    Classification logic (evaluated in order):
    1. EMERGENCY: Already filtered by rules.py — never returned here.
    2. URGENT: Any severe symptom present.
    3. URGENT: Two or more moderate symptoms.
    4. URGENT: One moderate symptom alongside 3+ total symptoms.
    5. URGENT: Low extraction confidence (safe default).
    6. ROUTINE: All other presentations.

    Args:
        extracted: Normalized symptoms from the normalizer.

    Returns:
        UrgencyLevel.URGENT or UrgencyLevel.ROUTINE.
        EMERGENCY is never returned here; it is reserved for rules.py.
    """
    all_symptoms = extracted.primary_symptoms + extracted.associated_symptoms

    if not all_symptoms:
        logger.info("No symptoms to classify — defaulting to ROUTINE")
        return UrgencyLevel.ROUTINE

    severe_count = sum(1 for s in all_symptoms if s.severity == Severity.SEVERE)
    moderate_count = sum(1 for s in all_symptoms if s.severity == Severity.MODERATE)
    total_symptoms = len(all_symptoms)

    logger.debug(
        "Classifying urgency",
        total=total_symptoms,
        severe=severe_count,
        moderate=moderate_count,
        confidence=extracted.confidence,
    )

    if severe_count >= _MIN_SEVERE_FOR_URGENT:
        logger.info("Severe symptom(s) present → URGENT", count=severe_count)
        return UrgencyLevel.URGENT

    if moderate_count >= _MIN_MODERATE_FOR_URGENT:
        logger.info("Multiple moderate symptoms → URGENT", count=moderate_count)
        return UrgencyLevel.URGENT

    if moderate_count >= 1 and total_symptoms >= _MIN_TOTAL_WITH_MODERATE_FOR_URGENT:
        logger.info(
            "Moderate symptom alongside multiple complaints → URGENT",
            moderate=moderate_count,
            total=total_symptoms,
        )
        return UrgencyLevel.URGENT

    if extracted.confidence < _LOW_CONFIDENCE_THRESHOLD:
        logger.info(
            "Low extraction confidence → URGENT (erring on side of caution)",
            confidence=extracted.confidence,
        )
        return UrgencyLevel.URGENT

    logger.info("Symptoms do not meet urgent threshold → ROUTINE")
    return UrgencyLevel.ROUTINE
