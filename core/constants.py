# core/constants.py
"""Constants for the overall system"""

# Standard Imports
from enum import Enum


## Triage Conversion States
class TriageState(str, Enum):
    """States for the conversation state machine."""
    IDLE = "idle"
    GATHERING = "gathering"
    ANALYZING = "analyzing"
    COMPLETED = "completed"


## Triage Classification

class UrgencyLevel(str, Enum):
    """Urgency levels for triage classification."""
    EMERGENCY = "emergency"
    URGENT = "urgent"
    ROUTINE = "routine"

class Department(str, Enum):
    """Hospital departments for patient routing.

    These are the CLINICAL destinations a patient is sent to.
    Department.EMERGENCY has been intentionally removed — it was never a real
    ward. How fast a patient needs to get there is carried by UrgencyLevel
    (EMERGENCY / URGENT / ROUTINE). The department here tells them which
    clinical team to ask for when they arrive.
    """
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


class Severity(str, Enum):
    """Severity levels for patient assessment."""
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"


## Triage Disclaimer
TRIAGE_DISCLAIMER = (
    "This is an AI-assisted medical system and not a medical diagnosis. "
    "If you are experiencing a medical emergency, please call emergency services immediately. "
)


## Critical Symptoms (Emergency Override)
#
# Any symptom in this set forces UrgencyLevel.EMERGENCY regardless of severity or
# any other classification logic. These are UNAMBIGUOUS, immediately life-threatening
# presentations where any delay risks death.
#
# FIX (Bug B): Removed "chest_pain" and "shortness_of_breath" from this set.
# These are HIGH-PRIORITY symptoms, but not unconditionally emergencies.
# A mild chest wall strain, musculoskeletal ache, or anxiety-related SOB routed
# straight to Emergency would overcrowd the ED and is clinically incorrect.
# These now escalate via CRITICAL_SEVERITY_MARKERS ("severe" severity) instead,
# so "severe chest pain" → Emergency, but "mild chest tightness" → Cardiology outpatient.
#
# Kept here: conditions where ANY presentation, regardless of severity, is life-threatening
# (cardiac arrest, stroke, anaphylaxis, poisoning, etc.).
CRITICAL_SYMPTOMS: set[str] = {
    # Cardiac (unconditional — no mild presentation exists)
    "cardiac_arrest",
    "aortic_dissection",
    "ruptured_aneurysm",

    # Respiratory (unconditional airway emergencies)
    "choking",
    "difficulty_breathing",   # distinct from mild shortness_of_breath

    # Neurological
    "unconscious",
    "stroke_symptoms",
    "seizure",
    "meningitis_symptoms",

    # Trauma / Bleeding
    "heavy_bleeding",
    "uncontrolled_bleeding",
    "severe_head_injury",
    "spinal_injury",
    "limb_amputation",
    "eye_injury",
    "severe_burn",

    # Toxicological
    "poisoning",
    "overdose",
    "electric_shock",

    # Allergic
    "anaphylaxis",
    "severe_allergic_reaction",

    # Psychiatric (safety — immediate risk to life)
    "suicidal_ideation",

    # Metabolic / Systemic
    "diabetic_coma",
    "hypertensive_crisis",
    "pulmonary_embolism",
    "septic_shock",
    "eclampsia",

    # Environmental
    "hypothermia",
    "heat_stroke",
    "drowning",

    # Other
    "severe_abdominal_pain",
    "sudden_vision_loss",
    "sudden_hearing_loss",
}

# Severity-scoped emergency escalation.
#
# ONLY symptoms in this set escalate to Emergency when the LLM extracts severity="severe".
# A severe toothache is not an emergency. A severe chest_pain is.
#
# Previously this was CRITICAL_SEVERITY_MARKERS = {"severe"}, which matched ANY symptom
# the LLM rated as severe — including toothaches, back pain, and headaches from tension.
# That caused massive over-triage to the ED. Now the check is:
#   symptom.name in SEVERITY_ESCALATES_TO_EMERGENCY AND symptom.severity == Severity.SEVERE
SEVERITY_ESCALATES_TO_EMERGENCY: set[str] = {
    "chest_pain",
    "shortness_of_breath",
    "abdominal_pain",        # may indicate aortic aneurysm, ruptured organ
    "back_pain",             # may indicate aortic dissection at severe intensity
    "headache",              # thunderclap headache = subarachnoid haemorrhage
    "breathing_difficulty",
    "chest_tightness",
    "pelvic_pain",           # ectopic pregnancy at severe presentation
    # NOTE: arm_pain and jaw_pain intentionally excluded.
    # Cardiac referred pain in the arm/jaw is already caught because the patient
    # will ALSO report chest_pain (which IS in this set). If arm_pain at severe
    # severity were included here, a patient saying "I broke my arm, pain is 9/10"
    # would incorrectly trigger Emergency instead of Urgent Orthopedics.
}


## Urgent Symptoms (Urgent Override)
#
# Symptoms in this set force UrgencyLevel.URGENT regardless of the classifier's
# severity-count logic. These are serious conditions that need same-day care but are
# not immediately life-threatening.
#
# FIX (Bug E): This set was defined but never checked. It is now wired into
# rules.py via check_urgent_symptoms() and called from pipeline.py.
# This fixes the fracture → ROUTINE misclassification (test case 4).
URGENT_SYMPTOMS: set[str] = {
    # Cardiac (non-emergency presentations)
    "chest_pain",            # Moved here from CRITICAL_SYMPTOMS — urgent, not always emergency
    "shortness_of_breath",   # Moved here — urgent, severity escalates to emergency
    "heart_palpitations",
    "racing_heart",
    "irregular_heartbeat",
    "fainting",
    "chest_tightness",

    # Trauma — always needs same-day imaging/assessment
    "fracture",
    "broken_bone",
    "dislocation",
    "ligament_injury",
    "sprain",

    # Neurological (concerning but not immediately life-threatening)
    "headache",
    "migraine",
    "numbness",
    "weakness_in_limbs",
    "dizziness",
    "blackout",
    "facial_drooping",
    "speech_difficulty",
    "balance_problems",
    "tremor",

    # Respiratory (non-emergency)
    "wheezing",
    "coughing_blood",
    "breathing_difficulty",

    # Psychiatric
    "panic_attack",
    "self_harm",
    "hallucinations",
    "psychosis",

    # Urological
    "kidney_stones",
    "blood_in_urine",
    "testicular_pain",

    # GI
    "rectal_bleeding",
    "blood_in_stool",
    "jaundice",

    # Eye
    "eye_pain",
    "double_vision",
    "blurred_vision",
    "red_eye",
    "vision_loss",

    # Infectious
    "prolonged_fever",
    "meningitis_symptoms",

    # Vascular
    "deep_vein_thrombosis",
    "blood_clot",

    # Gynecology
    "vaginal_bleeding",
    "pelvic_pain",

    # Allergy
    "allergic_reaction",
    "hives",
}


# Symptom -> Department Mapping
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
    "arm_pain": Department.ORTHOPEDICS,
    "leg_pain": Department.ORTHOPEDICS,
    "muscle_pain": Department.ORTHOPEDICS,
    "sprain": Department.ORTHOPEDICS,
    "dislocation": Department.ORTHOPEDICS,
    "tendon_pain": Department.ORTHOPEDICS,
    "ligament_injury": Department.ORTHOPEDICS,
    "spine_pain": Department.ORTHOPEDICS,
    "sciatica": Department.ORTHOPEDICS,
    "swelling": Department.ORTHOPEDICS,

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

    # Pulmonology — SPECIALIST only; acute/mild respiratory goes to General Medicine
    # FIX (Bug F): Removed "cough" from Pulmonology. A simple cough with fever is a
    # General Medicine presentation. Pulmonology is for chronic or complex
    # respiratory disease. Only genuinely specialist-level symptoms remain here.
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

    # General Medicine — acute but non-specialist presentations
    "hypertension": Department.GENERAL_MEDICINE,
    "diabetes_follow_up": Department.GENERAL_MEDICINE,
    "routine_checkup": Department.GENERAL_MEDICINE,
    # FIX (Bug F): cough moved here from Pulmonology.
    # A cough alone (or with fever) is a General Medicine presentation.
    # The LLM will extract "chronic_cough" for patients who describe a long-standing issue,
    # which correctly routes to Pulmonology via the mapping above.
    "cough": Department.GENERAL_MEDICINE,

    # General Medicine (non-specialist, low-acuity presentations)
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

    # Critical symptoms — mapped to their CLINICAL department, not Department.EMERGENCY.
    # Department.EMERGENCY is not a ward patients walk into; it is an urgency signal.
    # The UrgencyLevel.EMERGENCY flag (set by rules.py) is what tells the patient
    # to go immediately. The department here tells them — and the ED triage desk —
    # WHICH clinical team needs to see them.
    "cardiac_arrest": Department.CARDIOLOGY,
    "aortic_dissection": Department.VASCULAR_SURGERY,
    "ruptured_aneurysm": Department.VASCULAR_SURGERY,
    "choking": Department.PULMONOLOGY,
    "difficulty_breathing": Department.PULMONOLOGY,
    "unconscious": Department.NEUROLOGY,
    "meningitis_symptoms": Department.NEUROLOGY,
    "heavy_bleeding": Department.HEMATOLOGY,
    "uncontrolled_bleeding": Department.HEMATOLOGY,
    "severe_head_injury": Department.NEUROLOGY,
    "spinal_injury": Department.ORTHOPEDICS,
    "limb_amputation": Department.ORTHOPEDICS,
    "eye_injury": Department.OPHTHALMOLOGY,
    "severe_burn": Department.DERMATOLOGY,
    "poisoning": Department.GENERAL_MEDICINE,
    "overdose": Department.PSYCHIATRY,
    "electric_shock": Department.CARDIOLOGY,
    "severe_allergic_reaction": Department.ALLERGY_IMMUNOLOGY,
    "diabetic_coma": Department.ENDOCRINOLOGY,
    "hypertensive_crisis": Department.CARDIOLOGY,
    "pulmonary_embolism": Department.PULMONOLOGY,
    "septic_shock": Department.INFECTIOUS_DISEASE,
    "eclampsia": Department.GYNECOLOGY,
    "hypothermia": Department.GENERAL_MEDICINE,
    "heat_stroke": Department.GENERAL_MEDICINE,
    "drowning": Department.PULMONOLOGY,
    "severe_abdominal_pain": Department.GASTROENTEROLOGY,
    "sudden_vision_loss": Department.OPHTHALMOLOGY,
    "sudden_hearing_loss": Department.ENT,
}

# Urgency -> Recommendation Mapping
URGENCY_RECOMMENDATION_MAP: dict[UrgencyLevel, str] = {
    UrgencyLevel.EMERGENCY: "Please visit the emergency department immediately.",
    UrgencyLevel.URGENT: "Please schedule a same-day consultation. If symptoms worsen, visit the emergency department.",
    UrgencyLevel.ROUTINE: "You can schedule a regular appointment. Monitor your symptoms and seek immediate care if they worsen.",
}
