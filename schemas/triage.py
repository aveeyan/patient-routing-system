# schemas/triage.py

"""Schemas for triage"""

# Standard Imports
from datetime import datetime, timezone
from typing import Optional

# Third Party Imports
from pydantic import BaseModel, Field

# Local Imports
from core.constants import Department, Severity, UrgencyLevel


class Symptom(BaseModel):
    """A single extracted symptom with metadata."""

    name: str = Field(
        description="Canonical symptom name (e.g., 'chest_pain', 'headache')",
        examples=["chest_pain", "toothache", "fever"],
    )
    severity: Severity = Field(
        description="Severity level of the symptom as reported or inferred from patient input",
    )
    duration: Optional[str] = Field(
        default=None,
        description="Duration reported by patient (e.g., '2 days', 'since morning')",
        examples=["2 days", "3 hours", "since last night"],
    )
    body_site: Optional[str] = Field(
        default=None,
        description="Body location if specified (e.g., 'left arm', 'lower back')",
        examples=["left arm", "lower back", "right knee"],
    )


class ExtractedSymptoms(BaseModel):
    """
    Structured output from the LLM extraction step.
    This is the handoff contract between ai/ and triage/.
    """

    primary_symptoms: list[Symptom] = Field(
        default_factory=list,
        description="Main symptoms extracted from patient input",
    )
    associated_symptoms: list[Symptom] = Field(
        default_factory=list,
        description="Secondary or associated symptoms mentioned",
    )
    negated_symptoms: list[str] = Field(
        default_factory=list,
        description="Symptoms the patient explicitly denied having",
        examples=[["nausea", "fever"]],
    )
    raw_text: str = Field(
        description="Original user message that was processed",
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="LLM self-reported confidence in the extraction (0.0 to 1.0)",
    )
    low_confidence_reason: Optional[str] = Field(
        default=None,
        description=(
            "Explanation for low confidence scores, such as ambiguous language, "
            "missing context, or conflicting symptom descriptions. "
            "Should be populated when confidence is below 0.7."
        ),
    )


class TriageDecision(BaseModel):
    """Final triage output produced by the rule engine."""

    urgency: UrgencyLevel = Field(
        description="Classified urgency level",
    )
    severity: Severity = Field(
        description="Overall severity assessment that informed the urgency classification",
    )
    department: Department = Field(
        description="Recommended hospital department",
    )
    recommendation: str = Field(
        description="Human-readable action recommendation",
    )
    disclaimer: str = Field(
        description="Medical disclaimer for safety compliance",
    )
    is_critical_override: bool = Field(
        default=False,
        description="True if a critical safety rule forced the Emergency classification",
    )


class EncounterSummary(BaseModel):
    """HMIS-flavored structured encounter summary for interoperability."""

    session_id: str = Field(
        description="Unique session identifier",
    )
    chief_complaint: str = Field(
        description="Primary symptom in plain language",
    )
    urgency: UrgencyLevel = Field(
        description="Classified urgency level",
    )
    severity: Severity = Field(
        description="Overall severity assessment at the time of triage decision",
    )
    service_type: Department = Field(
        description="Recommended department/service type",
    )
    triage_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the triage decision was made (defaults to current UTC time)",
    )
    extracted_symptoms: list[str] = Field(
        default_factory=list,
        description="Canonical symptom names extracted during the session",
    )
    conversation_turns: int = Field(
        default=0,
        ge=0,
        description="Number of user-bot exchanges in the session",
    )
