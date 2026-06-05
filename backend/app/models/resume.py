"""Resume model for storing uploaded resumes."""
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class ResumeStatus(str, Enum):
    """Resume processing status."""

    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Resume(Base):
    """Resume model for storing user resumes."""

    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Parsed resume data
    parsed_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    parsed_data: Mapped[dict | None] = mapped_column(nullable=True)

    # Status tracking
    status: Mapped[str] = mapped_column(
        String(50),
        default=ResumeStatus.UPLOADED.value,
        nullable=False,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ATS Score
    ats_score: Mapped[float | None] = mapped_column(nullable=True)
    ats_breakdown: Mapped[dict | None] = mapped_column(nullable=True)

    # Metadata
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

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
    user: Mapped["User"] = relationship("User", back_populates="resumes")

    __table_args__ = (
        Index("ix_resumes_user_id", "user_id"),
        Index("ix_resumes_status", "status"),
        Index("ix_resumes_created_at", "created_at"),
        Index("ix_resumes_content_hash", "content_hash"),
    )

    def __repr__(self) -> str:
        return f"<Resume(id={self.id}, filename={self.filename}, status={self.status})>"
