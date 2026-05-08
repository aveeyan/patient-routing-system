# core/constants.py
"""Constants for the overall system"""

# Standard Imports
from enum import StrEnum


## Triage Conversion States
class TriageState(StrEnum):
    """States for the conversation state machine."""
    IDLE = "idle"
    GATHERING = "gathering"
    ANALYZING = "analyzing"
    TRIAGE_DECISION = "triage_decision"
    COMPLETED = "completed"


## Triage Classification
#
# Urgency Levels
class UrgencyLevel(StrEnum):
    """Urgency levels for triage classification."""
    EMERGENCY = "emergency"
    URGENT = "urgent"
    ROUTINE = "routine"

# Departments
class Department(StrEnum):
    """Hospital departments for patient routing."""
    EMERGENCY = "emergency"
    CARDIOLOGY = "cardiology"
    DENTAL = "dental"
    ORTHOPEDICS = "orthopedics"
    GENERAL_MEDICINE = "general_medicine"
    ENT = "ent"
    NEUROLOGY = "neurology"
    GASTROENTEROLOGY = "gastroenterology"
    PULMONOLOGY = "pulmonology"
    GYNECOLOGY = "gynecology"
    DERMATOLOGY = "dermatology"
    UROLOGY = "urology"
    OPHTHALMOLOGY = "ophthalmology"
    ENDOCRINOLOGY = "endocrinology"
    PSYCHIATRY = "psychiatry"
    NEPHROLOGY = "nephrology"
    RHEUMATOLOGY = "rheumatology"
    ONCOLOGY = "oncology"
    HEMATOLOGY = "hematology"
    VASCULAR_SURGERY = "vascular_surgery"
    PEDIATRICS = "pediatrics"
    GERIATRICS = "geriatrics"
    INFECTIOUS_DISEASE = "infectious_disease"
    ALLERGY_IMMUNOLOGY = "allergy_immunology"


## Severity Levels
class Severity(StrEnum):
    """Severity levels for patient assessment."""
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"


## Triage Disclaimer
TRIAGE_DISCLAIMER = (
    "This is an AI-assisted medical system and not a medical diagnosis. "
    "If you are experiencing a medical emergency, please call emergency services immediately. "
)


## Critical Symptoms (Safety Override)

# List of symptoms
CRITICAL_SYMPTOMS: set[str] = {
    "chest_pain",
    "severe_chest_pain",
    "difficulty_breathing",
    "unconscious",
    "severe_burn",
    "seizure",
    "stroke_symptoms",
    "heavy_bleeding",
    "uncontrolled_bleeding",
    "poisoning",
    "anaphylaxis",
    "suicidal_ideation",
    "cardiac_arrest",
    "choking",
    "drowning",
    "severe_allergic_reaction",
    "severe_head_injury",
    "spinal_injury",
    "overdose",
    "eclampsia",
    "diabetic_coma",
    "hypertensive_crisis",
    "ruptured_aneurysm",
    "aortic_dissection",
    "pulmonary_embolism",
    "septic_shock",
    "meningitis_symptoms",
    "severe_abdominal_pain",
    "sudden_vision_loss",
    "sudden_hearing_loss",
    "limb_amputation",
    "eye_injury",
    "electric_shock",
    "hypothermia",
    "heat_stroke",
}

# Critical severity markers
CRITICAL_SEVERITY_MARKERS: set[str] = {
    "severe",
    "unbearable",
    "life_threatening",
    "cannot_breathe",
    "unconscious",
    "sudden_onset",
    "worst_ever",
    "crushing",
    "tearing",
    "excruciating",
    "unresponsive",
    "paralyzed",
    "profuse",
    "unstoppable",
}

# Symptoms -> Department Mapping
SYMPTOM_DEPARTMENT_MAP: dict[str, Department] = {

    # Cardiology / Emergency
    "chest_pain": Department.CARDIOLOGY,
    "heart_palpitations": Department.CARDIOLOGY,
    "shortness_of_breath": Department.CARDIOLOGY,
    "irregular_heartbeat": Department.CARDIOLOGY,
    "chest_tightness": Department.CARDIOLOGY,
    "racing_heart": Department.CARDIOLOGY,
    "slow_heart_rate": Department.CARDIOLOGY,
    "heart_murmur": Department.CARDIOLOGY,
    "ankle_swelling": Department.CARDIOLOGY,
    "leg_swelling": Department.CARDIOLOGY,
    "fainting": Department.CARDIOLOGY,

    # Dental
    "tooth_pain": Department.DENTAL,
    "toothache": Department.DENTAL,
    "gum_pain": Department.DENTAL,
    "dental_pain": Department.DENTAL,
    "broken_tooth": Department.DENTAL,
    "lost_tooth": Department.DENTAL,
    "gum_bleeding": Department.DENTAL,
    "jaw_pain": Department.DENTAL,
    "mouth_sore": Department.DENTAL,
    "tooth_sensitivity": Department.DENTAL,
    "swollen_gums": Department.DENTAL,

    # Orthopedics
    "fracture": Department.ORTHOPEDICS,
    "broken_bone": Department.ORTHOPEDICS,
    "joint_pain": Department.ORTHOPEDICS,
    "back_pain": Department.ORTHOPEDICS,
    "neck_pain": Department.ORTHOPEDICS,
    "bone_pain": Department.ORTHOPEDICS,
    "knee_pain": Department.ORTHOPEDICS,
    "shoulder_pain": Department.ORTHOPEDICS,
    "hip_pain": Department.ORTHOPEDICS,
    "wrist_pain": Department.ORTHOPEDICS,
    "ankle_pain": Department.ORTHOPEDICS,
    "elbow_pain": Department.ORTHOPEDICS,
    "muscle_pain": Department.ORTHOPEDICS,
    "sprain": Department.ORTHOPEDICS,
    "dislocation": Department.ORTHOPEDICS,
    "tendon_pain": Department.ORTHOPEDICS,
    "ligament_injury": Department.ORTHOPEDICS,
    "spine_pain": Department.ORTHOPEDICS,
    "sciatica": Department.ORTHOPEDICS,

    # ENT
    "ear_pain": Department.ENT,
    "sore_throat": Department.ENT,
    "hearing_loss": Department.ENT,
    "sinus_pain": Department.ENT,
    "nasal_congestion": Department.ENT,
    "nosebleed": Department.ENT,
    "voice_hoarseness": Department.ENT,
    "tinnitus": Department.ENT,
    "ear_discharge": Department.ENT,
    "swallowing_difficulty": Department.ENT,
    "loss_of_smell": Department.ENT,
    "loss_of_taste": Department.ENT,
    "throat_lump": Department.ENT,
    "snoring": Department.ENT,
    "sleep_apnea": Department.ENT,

    # Neurology
    "headache": Department.NEUROLOGY,
    "migraine": Department.NEUROLOGY,
    "dizziness": Department.NEUROLOGY,
    "numbness": Department.NEUROLOGY,
    "tremor": Department.NEUROLOGY,
    "memory_loss": Department.NEUROLOGY,
    "confusion": Department.NEUROLOGY,
    "balance_problems": Department.NEUROLOGY,
    "facial_drooping": Department.NEUROLOGY,
    "speech_difficulty": Department.NEUROLOGY,
    "weakness_in_limbs": Department.NEUROLOGY,
    "tingling": Department.NEUROLOGY,
    "loss_of_coordination": Department.NEUROLOGY,
    "blackout": Department.NEUROLOGY,
    "stroke_symptoms": Department.NEUROLOGY,
    "seizure": Department.NEUROLOGY,

    # Gastroenterology
    "abdominal_pain": Department.GASTROENTEROLOGY,
    "nausea": Department.GASTROENTEROLOGY,
    "vomiting": Department.GASTROENTEROLOGY,
    "diarrhea": Department.GASTROENTEROLOGY,
    "constipation": Department.GASTROENTEROLOGY,
    "bloating": Department.GASTROENTEROLOGY,
    "heartburn": Department.GASTROENTEROLOGY,
    "acid_reflux": Department.GASTROENTEROLOGY,
    "rectal_bleeding": Department.GASTROENTEROLOGY,
    "blood_in_stool": Department.GASTROENTEROLOGY,
    "jaundice": Department.GASTROENTEROLOGY,
    "loss_of_appetite": Department.GASTROENTEROLOGY,
    "difficulty_swallowing": Department.GASTROENTEROLOGY,
    "stomach_cramps": Department.GASTROENTEROLOGY,
    "indigestion": Department.GASTROENTEROLOGY,
    "hemorrhoids": Department.GASTROENTEROLOGY,

    # Pulmonology
    "cough": Department.PULMONOLOGY,
    "wheezing": Department.PULMONOLOGY,
    "chronic_cough": Department.PULMONOLOGY,
    "coughing_blood": Department.PULMONOLOGY,
    "night_sweats": Department.PULMONOLOGY,
    "breathing_difficulty": Department.PULMONOLOGY,
    "chest_congestion": Department.PULMONOLOGY,
    "sleep_disordered_breathing": Department.PULMONOLOGY,
    "oxygen_saturation_low": Department.PULMONOLOGY,
    "hyperventilation": Department.PULMONOLOGY,
    # Dermatology
    "rash": Department.DERMATOLOGY,
    "skin_rash": Department.DERMATOLOGY,
    "itching": Department.DERMATOLOGY,
    "hives": Department.DERMATOLOGY,
    "eczema": Department.DERMATOLOGY,
    "psoriasis": Department.DERMATOLOGY,
    "acne": Department.DERMATOLOGY,
    "skin_lesion": Department.DERMATOLOGY,
    "mole_change": Department.DERMATOLOGY,
    "hair_loss": Department.DERMATOLOGY,
    "nail_change": Department.DERMATOLOGY,
    "wound_infection": Department.DERMATOLOGY,
    "skin_discoloration": Department.DERMATOLOGY,
    "blistering": Department.DERMATOLOGY,
    "excessive_sweating": Department.DERMATOLOGY,

    # Urology
    "painful_urination": Department.UROLOGY,
    "frequent_urination": Department.UROLOGY,
    "blood_in_urine": Department.UROLOGY,
    "urinary_incontinence": Department.UROLOGY,
    "kidney_pain": Department.UROLOGY,
    "groin_pain": Department.UROLOGY,
    "testicular_pain": Department.UROLOGY,
    "erectile_dysfunction": Department.UROLOGY,
    "urinary_retention": Department.UROLOGY,
    "kidney_stones": Department.UROLOGY,

    # Ophthalmology
    "eye_pain": Department.OPHTHALMOLOGY,
    "blurred_vision": Department.OPHTHALMOLOGY,
    "double_vision": Department.OPHTHALMOLOGY,
    "red_eye": Department.OPHTHALMOLOGY,
    "eye_discharge": Department.OPHTHALMOLOGY,
    "light_sensitivity": Department.OPHTHALMOLOGY,
    "floaters": Department.OPHTHALMOLOGY,
    "vision_loss": Department.OPHTHALMOLOGY,
    "dry_eyes": Department.OPHTHALMOLOGY,
    "eye_swelling": Department.OPHTHALMOLOGY,

    # Endocrinology
    "excessive_thirst": Department.ENDOCRINOLOGY,
    "excessive_hunger": Department.ENDOCRINOLOGY,
    "unexplained_weight_loss": Department.ENDOCRINOLOGY,
    "unexplained_weight_gain": Department.ENDOCRINOLOGY,
    "heat_intolerance": Department.ENDOCRINOLOGY,
    "cold_intolerance": Department.ENDOCRINOLOGY,
    "thyroid_swelling": Department.ENDOCRINOLOGY,
    "blood_sugar_abnormality": Department.ENDOCRINOLOGY,
    "hormonal_imbalance": Department.ENDOCRINOLOGY,
    "adrenal_symptoms": Department.ENDOCRINOLOGY,

    # Psychiatry
    "suicidal_ideation": Department.PSYCHIATRY,
    "anxiety": Department.PSYCHIATRY,
    "depression": Department.PSYCHIATRY,
    "panic_attack": Department.PSYCHIATRY,
    "hallucinations": Department.PSYCHIATRY,
    "delusions": Department.PSYCHIATRY,
    "psychosis": Department.PSYCHIATRY,
    "self_harm": Department.PSYCHIATRY,
    "eating_disorder": Department.PSYCHIATRY,
    "sleep_disorder": Department.PSYCHIATRY,
    "mood_swings": Department.PSYCHIATRY,
    "substance_abuse": Department.PSYCHIATRY,

    # Nephrology
    "kidney_failure": Department.NEPHROLOGY,
    "decreased_urine_output": Department.NEPHROLOGY,
    "swollen_face": Department.NEPHROLOGY,
    "protein_in_urine": Department.NEPHROLOGY,
    "dialysis_related": Department.NEPHROLOGY,

    # Rheumatology
    "joint_swelling": Department.RHEUMATOLOGY,
    "joint_stiffness": Department.RHEUMATOLOGY,
    "autoimmune_symptoms": Department.RHEUMATOLOGY,
    "lupus_symptoms": Department.RHEUMATOLOGY,
    "gout": Department.RHEUMATOLOGY,
    "fibromyalgia": Department.RHEUMATOLOGY,
    "morning_stiffness": Department.RHEUMATOLOGY,

    # Gynecology
    "pelvic_pain": Department.GYNECOLOGY,
    "irregular_periods": Department.GYNECOLOGY,
    "vaginal_discharge": Department.GYNECOLOGY,
    "vaginal_bleeding": Department.GYNECOLOGY,
    "menstrual_pain": Department.GYNECOLOGY,
    "breast_lump": Department.GYNECOLOGY,
    "breast_pain": Department.GYNECOLOGY,
    "pregnancy_related": Department.GYNECOLOGY,
    "menopausal_symptoms": Department.GYNECOLOGY,

    # Hematology
    "easy_bruising": Department.HEMATOLOGY,
    "prolonged_bleeding": Department.HEMATOLOGY,
    "anemia_symptoms": Department.HEMATOLOGY,
    "swollen_lymph_nodes": Department.HEMATOLOGY,
    "blood_clot": Department.HEMATOLOGY,

    # Vascular Surgery
    "leg_ulcer": Department.VASCULAR_SURGERY,
    "varicose_veins": Department.VASCULAR_SURGERY,
    "cold_extremities": Department.VASCULAR_SURGERY,
    "peripheral_artery_pain": Department.VASCULAR_SURGERY,
    "deep_vein_thrombosis": Department.VASCULAR_SURGERY,

    # Pediatrics
    "child_fever": Department.PEDIATRICS,
    "child_rash": Department.PEDIATRICS,
    "child_vomiting": Department.PEDIATRICS,
    "child_diarrhea": Department.PEDIATRICS,
    "child_breathing_difficulty": Department.PEDIATRICS,
    "growth_concern": Department.PEDIATRICS,
    "vaccination_related": Department.PEDIATRICS,

    # Infectious Disease
    "prolonged_fever": Department.INFECTIOUS_DISEASE,
    "malaria_symptoms": Department.INFECTIOUS_DISEASE,
    "dengue_symptoms": Department.INFECTIOUS_DISEASE,
    "typhoid_symptoms": Department.INFECTIOUS_DISEASE,
    "hiv_related": Department.INFECTIOUS_DISEASE,
    "tuberculosis_symptoms": Department.INFECTIOUS_DISEASE,
    "travel_related_illness": Department.INFECTIOUS_DISEASE,
    "sexually_transmitted_infection": Department.INFECTIOUS_DISEASE,

    # Allergy and Immunology
    "allergic_reaction": Department.ALLERGY_IMMUNOLOGY,
    "anaphylaxis": Department.ALLERGY_IMMUNOLOGY,
    "chronic_allergies": Department.ALLERGY_IMMUNOLOGY,
    "food_allergy": Department.ALLERGY_IMMUNOLOGY,
    "drug_allergy": Department.ALLERGY_IMMUNOLOGY,
    "insect_sting_reaction": Department.ALLERGY_IMMUNOLOGY,
    "immune_deficiency": Department.ALLERGY_IMMUNOLOGY,

    # General Medicine (default fallback)
    "fever": Department.GENERAL_MEDICINE,
    "fatigue": Department.GENERAL_MEDICINE,
    "cold": Department.GENERAL_MEDICINE,
    "flu": Department.GENERAL_MEDICINE,
    "body_ache": Department.GENERAL_MEDICINE,
    "general_weakness": Department.GENERAL_MEDICINE,
    "malaise": Department.GENERAL_MEDICINE,
    "dehydration": Department.GENERAL_MEDICINE,
    "insomnia": Department.GENERAL_MEDICINE,
    "weight_change": Department.GENERAL_MEDICINE,
    "hypertension": Department.GENERAL_MEDICINE,
    "diabetes_follow_up": Department.GENERAL_MEDICINE,
    "routine_checkup": Department.GENERAL_MEDICINE,
}

# Urgency -> Recommendation Mapping
URGENCY_RECOMMENDATION_MAP: dict[UrgencyLevel, str] = {
    UrgencyLevel.EMERGENCY: "Please visit the emergency department immediately.",
    UrgencyLevel.URGENT: "Please schedule a same-day consultation. If symptoms worsen, visit the emergency department.",
    UrgencyLevel.ROUTINE: "You can schedule a regular appointment. Monitor your symptoms and seek immediate care if they worsen.",
}
