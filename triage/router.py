# triage/router.py

"""Symptom-to-department router for triage decisions."""

# Third Party Imports
from loguru import logger

# Local Imports
from core.constants import Department, SYMPTOM_DEPARTMENT_MAP
from schemas.triage import ExtractedSymptoms, Symptom


## Routing Fallback
# When no symptom maps to a known department, the router falls back to general Medicine for safe, non-emergency handling.
_FALLBACK_DEPARTMENT = Department.GENERAL_MEDICINE


## Department Priority
# When multiple symptoms map to different departments, the department with the lowest index in this list wins.
_DEPARTMENT_PRIORITY: list[Department] = [
    Department.EMERGENCY,
    Department.CARDIOLOGY,
    Department.NEUROLOGY,
    Department.PULMONOLOGY,
    Department.GASTROENTEROLOGY,
    Department.UROLOGY,
    Department.ORTHOPEDICS,
    Department.ENT,
    Department.OPHTHALMOLOGY,
    Department.DENTAL,
    Department.DERMATOLOGY,
    Department.GYNECOLOGY,
    Department.PSYCHIATRY,
    Department.ENDOCRINOLOGY,
    Department.NEPHROLOGY,
    Department.RHEUMATOLOGY,
    Department.HEMATOLOGY,
    Department.VASCULAR_SURGERY,
    Department.INFECTIOUS_DISEASE,
    Department.ALLERGY_IMMUNOLOGY,
    Department.ONCOLOGY,
    Department.PEDIATRICS,
    Department.GERIATRICS,
    Department.GENERAL_MEDICINE,
]


## Startup Integrity Check
# Ensures every Department value is represented in _DEPARTMENT_PRIORITY.
# Catches drift when new departments are added to constants.py.
def _validate_priority_list() -> None:
    all_departments = set(Department)
    prioritized = set(_DEPARTMENT_PRIORITY)
    missing = all_departments - prioritized
    if missing:
        raise ValueError(
            "_DEPARTMENT_PRIORITY is missing department(s): "
            + ", ".join(str(d) for d in missing)
        )

_validate_priority_list()


## Public API

def route_to_department(extracted: ExtractedSymptoms) -> tuple[Department, list[Department]]:
    """Map extracted symptoms to the most appropriate department.

    Uses primary symptoms first for routing; falls back to associated
    symptoms if no primary symptom maps to a known department.
    Negated symptoms are excluded from routing in both lists.

    Priority rules:
    1. Primary symptoms represent the chief complaint and are checked first.
    2. If multiple departments match, the highest-priority department wins.
    3. If no primary symptom maps, associated symptoms are used.
    4. If nothing maps, General Medicine is returned as the safe fallback.

    Args:
        extracted: Normalized symptoms from the normalizer.

    Returns:
        A tuple of (selected_department, all_matching_departments).
        The list provides full routing context for observability.
    """
    negated = set(extracted.negated_symptoms)

    active_primary = [s for s in extracted.primary_symptoms if s.name not in negated]
    active_associated = [s for s in extracted.associated_symptoms if s.name not in negated]

    primary_matches = _deduplicate(_get_department_matches(active_primary))
    associated_matches = _deduplicate(_get_department_matches(active_associated))

    if primary_matches:
        selected = _select_highest_priority(primary_matches)
        all_matches = _deduplicate(primary_matches + associated_matches)

        logger.info(
            "Department routed from primary symptoms",
            primary_matches=primary_matches,
            associated_matches=associated_matches,
            selected=selected,
        )
        return selected, all_matches

    if associated_matches:
        selected = _select_highest_priority(associated_matches)

        logger.info(
            "Department routed from associated symptoms",
            matches=associated_matches,
            selected=selected,
        )
        return selected, associated_matches

    logger.warning(
        "No symptoms matched any department, falling back to General Medicine",
        primary_count=len(active_primary),
        associated_count=len(active_associated),
        primary_names=[s.name for s in active_primary],
        associated_names=[s.name for s in active_associated],
    )
    return _FALLBACK_DEPARTMENT, [_FALLBACK_DEPARTMENT]


## Private Helpers

def _get_department_matches(symptoms: list[Symptom]) -> list[Department]:
    """Map a list of symptoms to their departments.

    Symptoms that do not match any key in SYMPTOM_DEPARTMENT_MAP
    are skipped with a debug log.
    """
    departments: list[Department] = []

    for symptom in symptoms:
        dept = SYMPTOM_DEPARTMENT_MAP.get(symptom.name)
        if dept is not None:
            departments.append(dept)
        else:
            logger.debug(
                "Symptom has no department mapping",
                name=symptom.name,
            )

    return departments


def _select_highest_priority(departments: list[Department]) -> Department:
    """Select the highest-priority department from a deduplicated list.

    Uses the _DEPARTMENT_PRIORITY ordering. Lower index = higher priority.
    Departments not found in the priority list are ranked last.
    """
    if len(departments) == 1:
        return departments[0]

    priority_map = {dept: idx for idx, dept in enumerate(_DEPARTMENT_PRIORITY)}
    return min(departments, key=lambda d: priority_map.get(d, len(_DEPARTMENT_PRIORITY)))


def _deduplicate(departments: list[Department]) -> list[Department]:
    """Remove duplicate departments while preserving insertion order."""
    seen: set[Department] = set()
    result: list[Department] = []

    for dept in departments:
        if dept not in seen:
            seen.add(dept)
            result.append(dept)

    return result
