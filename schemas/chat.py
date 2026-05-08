# schemas/chat.py

"""Schemas for chat interactions."""

# Standard Imports
from datetime import datetime, timezone
from typing import Literal, Optional

# Third Party Imports
from pydantic import BaseModel, Field, model_validator

# Local Imports
from core.constants import TriageState
from schemas.triage import EncounterSummary, ExtractedSymptoms, TriageDecision


## Request Schemas

class MessageRequest(BaseModel):
    """Incoming message from the patient."""

    session_id: str = Field(
        description="Session ID returned by /triage/start",
    )
    message: str = Field(
        min_length=1,
        max_length=2000,
        description="Patient's message text",
    )


## Response Schemas

class StartSessionResponse(BaseModel):
    """Response after creating a new triage session."""

    session_id: str = Field(
        description="Unique session identifier for subsequent messages",
    )
    state: TriageState = Field(
        default=TriageState.IDLE,
        description="Initial session state",
    )
    message: str = Field(
        description="Welcome message and opening prompt from the bot",
    )


class BotResponse(BaseModel):
    """Response to a patient message.

    This is a union-type response:
    - When state is GATHERING: contains follow-up question and extracted data
    - When state is COMPLETED: contains the final triage decision
    """

    session_id: str = Field(
        description="Session identifier",
    )
    state: TriageState = Field(
        description="Current state of the conversation",
    )
    bot_message: str = Field(
        description="Bot's response text (follow-up question or recommendation)",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC timestamp of when this response was generated",
    )
    extracted_so_far: Optional[ExtractedSymptoms] = Field(
        default=None,
        description="Symptoms extracted so far (provided during GATHERING state)",
    )
    triage: Optional[TriageDecision] = Field(
        default=None,
        description="Final triage decision (provided when state is COMPLETED)",
    )
    encounter_summary: Optional[EncounterSummary] = Field(
        default=None,
        description="HMIS-compatible encounter summary (provided when state is COMPLETED)",
    )


class MessageTurn(BaseModel):
    """A single turn in the conversation history."""

    role: Literal["user", "bot"] = Field(
        description="Who sent this message",
    )
    content: str = Field(
        description="Message content",
    )
    timestamp: datetime = Field(
        description="When this message was sent",
    )


class SessionHistoryResponse(BaseModel):
    """Full history of a triage session."""

    session_id: str = Field(
        description="Session identifier",
    )
    state: TriageState = Field(
        description="Current session state",
    )
    messages: list[MessageTurn] = Field(
        default_factory=list,
        description="All user-bot message turns in chronological order",
    )
    triage: Optional[TriageDecision] = Field(
        default=None,
        description="Triage decision if completed",
    )
    created_at: datetime = Field(
        description="Session creation timestamp",
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Session completion timestamp",
    )


class SessionListItem(BaseModel):
    """Summary item for the sessions list endpoint."""

    session_id: str = Field(
        description="Session identifier",
    )
    state: TriageState = Field(
        description="Current session state",
    )
    created_at: datetime = Field(
        description="Session creation timestamp",
    )
    summary: Optional[str] = Field(
        default=None,
        description="The patient's first message, truncated to 200 characters, used as a brief session preview",
    )


class SessionListResponse(BaseModel):
    """List of all sessions."""

    sessions: list[SessionListItem] = Field(
        default_factory=list,
    )
    total: int = Field(
        default=0,
        description="Total number of sessions, always equal to len(sessions)",
    )

    @model_validator(mode="after")
    def sync_total(self) -> "SessionListResponse":
        self.total = len(self.sessions)
        return self
