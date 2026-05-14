# triage/normalizer.py

"""Normalizer for triage filter"""

# Third Party Imports
from loguru import logger

# Local Imports
from core.constants import SYMPTOM_DEPARTMENT_MAP
from schemas.triage import ExtractedSymptoms, Symptom

## Synonym Map
# Maps common layperson terms and LLM variants to canonical symptom names that exist as keys in core.constants.SYMPTOM_DEPARTMENT_MAP.
# Only include terms NOT already present as keys in that map.
SYNONYM_MAP: dict[str, str] = {
    # Cardiac / Respiratory
    "breathlessness": "shortness_of_breath",
    "cannot_breathe": "breathing_difficulty",
    "hard_to_breathe": "breathing_difficulty",
    "chest_discomfort": "chest_pain",
    "chest_pressure": "chest_pain",
    "heart_pain": "chest_pain",
    "racing_heartbeat": "racing_heart",
    "slow_heartbeat": "slow_heart_rate",
    "passing_out": "fainting",
    # Gastro
    "stomach_pain": "abdominal_pain",
    "stomach_ache": "abdominal_pain",
    "tummy_pain": "abdominal_pain",
    "belly_pain": "abdominal_pain",
    "feeling_sick": "nausea",
    "throwing_up": "vomiting",
    "puking": "vomiting",
    "loose_motion": "diarrhea",
    "loose_stool": "diarrhea",
    "runny_stool": "diarrhea",
    "acid_coming_up": "acid_reflux",
    "cant_swallow": "difficulty_swallowing",
    "trouble_swallowing": "difficulty_swallowing",
    # Dental
    "pain_in_tooth": "toothache",
    "cavity_pain": "toothache",
    "sensitive_tooth": "tooth_sensitivity",
    "bleeding_gums": "gum_bleeding",
    # Neuro
    "feeling_dizzy": "dizziness",
    "lightheaded": "dizziness",
    "vertigo": "dizziness",
    "pins_and_needles": "tingling",
    "cant_feel": "numbness",
    "loss_of_sensation": "numbness",
    "falling_over": "balance_problems",
    "slurred_speech": "speech_difficulty",
    "drooping_face": "facial_drooping",
    "forgetfulness": "memory_loss",
    # Trauma / Amputation / Bleeding
    "lost_a_finger": "limb_amputation",
    "lost_my_finger": "limb_amputation",
    "finger_cut_off": "limb_amputation",
    "finger_severed": "limb_amputation",
    "severed_finger": "limb_amputation",
    "lost_a_toe": "limb_amputation",
    "lost_my_toe": "limb_amputation",
    "lost_a_hand": "limb_amputation",
    "lost_my_hand": "limb_amputation",
    "lost_an_arm": "limb_amputation",
    "lost_my_arm": "limb_amputation",
    "lost_a_leg": "limb_amputation",
    "lost_my_leg": "limb_amputation",
    "limb_lost": "limb_amputation",
    "digit_amputation": "limb_amputation",
    "partial_amputation": "limb_amputation",
    "traumatic_amputation": "limb_amputation",
    "amputation": "limb_amputation",
    "bleeding_wont_stop": "uncontrolled_bleeding",
    "bleeding_not_stopping": "uncontrolled_bleeding",
    "cant_stop_bleeding": "uncontrolled_bleeding",
    "blood_not_stopping": "uncontrolled_bleeding",
    "bleeding_continuously": "uncontrolled_bleeding",
    "non_stop_bleeding": "uncontrolled_bleeding",
    "profuse_bleeding": "uncontrolled_bleeding",
    "severe_bleeding": "heavy_bleeding",
    "lots_of_blood": "heavy_bleeding",
    "bleeding_a_lot": "heavy_bleeding",
    "gushing_blood": "heavy_bleeding",
    "spurting_blood": "heavy_bleeding",
    # Ortho — Fractures
    "cracked_bone": "fracture",
    "bone_fracture": "fracture",
    "broken_arm": "fracture",
    "broke_my_arm": "fracture",
    "broke_arm": "fracture",
    "broken_leg": "fracture",
    "broke_my_leg": "fracture",
    "broke_leg": "fracture",
    "broken_wrist": "fracture",
    "broke_my_wrist": "fracture",
    "broken_hand": "fracture",
    "broken_finger": "fracture",
    "broken_toe": "fracture",
    "broken_foot": "fracture",
    "broken_ankle": "fracture",
    "broken_collarbone": "fracture",
    "broken_rib": "fracture",
    "broken_nose": "fracture",
    "broken_jaw": "fracture",
    "broken_hip": "fracture",
    "broken_knee": "fracture",
    "broken_elbow": "fracture",
    "broken_shoulder": "fracture",
    "snapped_bone": "fracture",
    "stress_fracture": "fracture",
    "hairline_fracture": "fracture",
    "compound_fracture": "fracture",
    "muscle_ache": "muscle_pain",
    "back_ache": "back_pain",
    "neck_ache": "neck_pain",
    "knee_swelling": "knee_pain",
    "twisted_ankle": "sprain",
    "twisted_wrist": "sprain",
    "torn_ligament": "ligament_injury",
    "torn_tendon": "tendon_pain",
    # ENT
    "earache": "ear_pain",
    "runny_nose": "nasal_congestion",
    "stuffy_nose": "nasal_congestion",
    "sinus_headache": "sinus_pain",
    "ringing_in_ears": "tinnitus",
    "cant_hear": "hearing_loss",
    "hoarse_voice": "voice_hoarseness",
    "pain_when_swallowing": "swallowing_difficulty",
    "cant_smell": "loss_of_smell",
    "cant_taste": "loss_of_taste",
    # Urology
    "hurts_to_pee": "painful_urination",
    "burning_urination": "painful_urination",
    "peeing_frequently": "frequent_urination",
    "blood_while_peeing": "blood_in_urine",
    "cant_hold_urine": "urinary_incontinence",
    "testicle_pain": "testicular_pain",
    "kidney_stone_pain": "kidney_stones",
    # Ophthalmology
    "blurry_vision": "blurred_vision",
    "seeing_double": "double_vision",
    "sensitive_to_light": "light_sensitivity",
    "itchy_eyes": "dry_eyes",
    "puffy_eyes": "eye_swelling",
    # Dermatology
    "itchy_skin": "itching",
    "skin_irritation": "rash",
    "red_skin": "rash",
    "hives_outbreak": "hives",
    "pimple": "acne",
    "zit": "acne",
    "balding": "hair_loss",
    "thinning_hair": "hair_loss",
    "sweating_excessively": "excessive_sweating",
    # Psychiatry
    "feeling_down": "depression",
    "hopeless": "depression",
    "nervousness": "anxiety",
    "freaking_out": "panic_attack",
    "hearing_things": "hallucinations",
    "seeing_things": "hallucinations",
    "moody": "mood_swings",
    "cutting_myself": "self_harm",
    "want_to_die": "suicidal_ideation",
    "suicidal_thoughts": "suicidal_ideation",
    # General
    "high_temp": "fever",
    "temperature": "fever",
    "feeling_weak": "general_weakness",
    "tiredness": "fatigue",
    "exhaustion": "fatigue",
    "worn_out": "fatigue",
    "body_pain": "body_ache",
    "whole_body_ache": "body_ache",
    "flu_symptoms": "flu",
    "common_cold": "cold",
    "cant_sleep": "insomnia",
    "trouble_sleeping": "insomnia",
    "high_blood_pressure": "hypertension",
    "losing_weight": "weight_change",
    "gaining_weight": "weight_change",
    # Gynecology
    "period_pain": "menstrual_pain",
    "cramps": "menstrual_pain",
    "heavy_period": "vaginal_bleeding",
    "spotting": "vaginal_bleeding",
    "lump_in_breast": "breast_lump",
    "sore_breast": "breast_pain",
    # Infectious Disease
    "long_fever": "prolonged_fever",
    "malaria": "malaria_symptoms",
    "dengue": "dengue_symptoms",
    "typhoid": "typhoid_symptoms",
    "tb": "tuberculosis_symptoms",
    "sti": "sexually_transmitted_infection",
    "std": "sexually_transmitted_infection",
    # Other
    "allergy_attack": "allergic_reaction",
    "severe_allergy": "anaphylaxis",
    "swollen_glands": "swollen_lymph_nodes",
    "bruise_easily": "easy_bruising",
    # Self Harm
    "suicidal": "suicidal_ideation",
    "feeling_suicidal": "suicidal_ideation",
    "i_am_suicidal": "suicidal_ideation",
    "feeling_like_dying": "suicidal_ideation",
    "dont_want_to_live": "suicidal_ideation",
    "don't_want_to_live": "suicidal_ideation",
    "no_will_to_live": "suicidal_ideation",
    "thinking_of_ending_it": "suicidal_ideation",
}


## Startup Integrity Check
# Validates that every target in SYNONYM_MAP resolves to a known canonical key.
# Runs once at import time so misconfiguration is caught immediately on startup.
def _validate_synonym_map() -> None:
    invalid: list[str] = [
        f"{alias!r} -> {target!r}"
        for alias, target in SYNONYM_MAP.items()
        if target not in SYMPTOM_DEPARTMENT_MAP
    ]
    if invalid:
        raise ValueError(
            "SYNONYM_MAP contains targets not present in SYMPTOM_DEPARTMENT_MAP:\n"
            + "\n".join(invalid)
        )


_validate_synonym_map()


## Public API


def normalize(extracted: ExtractedSymptoms) -> ExtractedSymptoms:
    """Normalize symptom names in an ExtractedSymptoms object.

    Args:
        extracted: The extracted symptoms from the AI layer.

    Returns:
        A new ExtractedSymptoms with normalized symptom names.
    """
    normalized_primary = [_normalize_symptom(s) for s in extracted.primary_symptoms]
    normalized_associated = [
        _normalize_symptom(s) for s in extracted.associated_symptoms
    ]
    normalized_negated = [
        _normalize_negated(name) for name in extracted.negated_symptoms
    ]

    return ExtractedSymptoms(
        primary_symptoms=normalized_primary,
        associated_symptoms=normalized_associated,
        negated_symptoms=normalized_negated,
        raw_text=extracted.raw_text,
        confidence=extracted.confidence,
        low_confidence_reason=extracted.low_confidence_reason,
    )


## Private Helpers


def _normalize_symptom(symptom: Symptom) -> Symptom:
    """Normalize a single Symptom's name using the synonym map.

    Returns a copy with the canonical name if a mapping exists.
    Logs a warning if the name is unknown to both maps.
    """
    clean_name = symptom.name.strip().lower()
    canonical = SYNONYM_MAP.get(clean_name, clean_name)

    if canonical != clean_name:
        logger.debug(
            "Normalized symptom",
            original=clean_name,
            normalized=canonical,
        )

    if canonical not in SYMPTOM_DEPARTMENT_MAP:
        logger.warning(
            "Unknown symptom after normalization, no department mapping found",
            name=canonical,
        )

    if canonical == clean_name:
        return symptom

    return symptom.model_copy(update={"name": canonical})


def _normalize_negated(name: str) -> str:
    """Normalize a single negated symptom name using the synonym map."""
    clean_name = name.strip().lower()
    canonical = SYNONYM_MAP.get(clean_name, clean_name)

    if canonical != clean_name:
        logger.debug(
            "Normalized negated symptom",
            original=clean_name,
            normalized=canonical,
        )

    return canonical
