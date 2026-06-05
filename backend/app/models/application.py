"""Application model for tracking job applications."""
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.job import Job
    from app.models.resume import Resume


class ApplicationStatus(str, Enum):
    """Application status enumeration."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    PHONE_SCREEN = "phone_screen"
    TECHNICAL = "technical"
    ONSITE = "onsite"
    OFFER = "offer"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class Application(Base):
    """Application model for tracking job applications."""

    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    resume_id: Mapped[int | None] = mapped_column(
        ForeignKey("resumes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(50),
        default=ApplicationStatus.SUBMITTED.value,
        nullable=False,
    )
    status_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ATS Scoring at application time
    ats_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    ats_breakdown: Mapped[dict | None] = mapped_column(nullable=True)

    # Cover letter
    cover_letter: Mapped[str | None] = mapped_column(Text, nullable=True)
    cover_letter_customized: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    # External tracking
    external_application_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    source: Mapped[str] = mapped_column(
        String(100),
        default="direct",
        nullable=False,
    )

    # Scheduling
    applied_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    interview_scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    offer_received_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Salary negotiation
    salary_offered: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_currency: Mapped[str] = mapped_column(String(10), default="USD")

    # Notes
    user_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    recruiter_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default_factory=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="applications")
    job: Mapped["Job"] = relationship("Job")
    resume: Mapped["Resume | None"] = relationship("Resume")

    __table_args__ = (
        Index("ix_applications_user_id", "user_id"),
        Index("ix_applications_job_id", "job_id"),
        Index("ix_applications_resume_id", "resume_id"),
        Index("ix_applications_status", "status"),
        Index("ix_applications_created_at", "created_at"),
        Index("ix_applications_applied_at", "applied_at"),
    )

    def __repr__(self) -> str:
        return f"<Application(id={self.id}, user_id={self.user_id}, job_id={self.job_id}, status={self.status})>"
