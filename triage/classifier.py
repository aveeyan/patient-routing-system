# triage/classifier.py

"""Classifier of Triage"""

# Third Party Imports
from loguru import logger

# Local Imports
from core.constants import Severity, UrgencyLevel
from schemas.triage import ExtractedSymptoms


## Classification Thresholds

_SEVERE_URGENT_THRESHOLD = 1
_MODERATE_URGENT_THRESHOLD = 2
_MODERATE_WITH_OTHERS_THRESHOLD = 3
_LOW_CONFIDENCE_THRESHOLD = 0.5


## Public API

def classify_urgency(extracted: ExtractedSymptoms) -> UrgencyLevel:
    """Classify the urgency level based on extracted symptoms.

    This is the decision engine for non-critical cases.
    Critical overrides are handled by rules.py BEFORE this is called.

    Classification logic:
    - EMERGENCY: Already filtered by rules.py. Should not reach here.
    - URGENT: Any severe symptom; multiple moderate symptoms; one moderate
              symptom among three or more total; or low extraction confidence.
    - ROUTINE: Single mild or moderate symptom with high confidence, or
               stable low-complexity presentations.

    Args:
        extracted: Normalized symptoms from the normalizer.

    Returns:
        UrgencyLevel classification (URGENT or ROUTINE).
        EMERGENCY is never returned here; it is reserved for rules.py.
    """
    all_symptoms = extracted.primary_symptoms + extracted.associated_symptoms

    if not all_symptoms:
        logger.info("No symptoms to classify - defaulting to ROUTINE")
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

    if severe_count >= _SEVERE_URGENT_THRESHOLD:
        logger.info("Severe symptom(s) present -> URGENT", count=severe_count)
        return UrgencyLevel.URGENT

    if moderate_count >= _MODERATE_URGENT_THRESHOLD:
        logger.info("Multiple moderate symptoms -> URGENT", count=moderate_count)
        return UrgencyLevel.URGENT

    if moderate_count >= 1 and total_symptoms >= _MODERATE_WITH_OTHERS_THRESHOLD:
        logger.info(
            "Moderate symptom alongside multiple complaints -> URGENT",
            moderate=moderate_count,
            total=total_symptoms,
        )
        return UrgencyLevel.URGENT

    if extracted.confidence < _LOW_CONFIDENCE_THRESHOLD:
        logger.info(
            "Low extraction confidence -> URGENT (erring on side of caution)",
            confidence=extracted.confidence,
        )
        return UrgencyLevel.URGENT

    logger.info("Symptoms do not meet urgent threshold -> ROUTINE")
    return UrgencyLevel.ROUTINE
