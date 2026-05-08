# db/models.py

"""Database Models"""

# Standard Imports
import uuid
from datetime import datetime

# Third Party Imports
from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# Local Imports
from core.constants import Department, Severity, TriageState, UrgencyLevel


## Base
class Base(DeclarativeBase):
    pass


## Models

# Session
class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    state: Mapped[TriageState] = mapped_column(
        Enum(TriageState),
        default=TriageState.IDLE,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="session",
        order_by="Message.created_at",
        cascade="all, delete-orphan",
    )
    triage_result: Mapped["TriageResult | None"] = relationship(
        "TriageResult",
        back_populates="session",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Session(id={self.id!r}, state={self.state!r})>"


# Message
class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        Enum("user", "bot", name="message_role"),
        nullable=False,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    extracted_symptoms: Mapped[dict | None] = mapped_column(
        SQLiteJSON,
        nullable=True,
    )
    triage_decision: Mapped[dict | None] = mapped_column(
        SQLiteJSON,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    session: Mapped["Session"] = relationship(
        "Session",
        back_populates="messages",
    )

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, role={self.role!r}, session_id={self.session_id!r})>"


class TriageResult(Base):
    __tablename__ = "triage_results"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    urgency: Mapped[UrgencyLevel] = mapped_column(
        Enum(UrgencyLevel),
        nullable=False,
    )
    severity: Mapped[Severity] = mapped_column(
        Enum(Severity),
        nullable=False,
    )
    department: Mapped[Department] = mapped_column(
        Enum(Department),
        nullable=False,
    )
    recommendation: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    disclaimer: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    is_critical_override: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    session: Mapped["Session"] = relationship(
        "Session",
        back_populates="triage_result",
    )

    def __repr__(self) -> str:
        return f"<TriageResult(session_id={self.session_id!r}, urgency={self.urgency!r})>"
