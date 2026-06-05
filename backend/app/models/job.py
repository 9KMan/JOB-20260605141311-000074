"""Job model for job listings."""
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, Boolean, DateTime, Text, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

if TYPE_CHECKING:
    pass


class JobStatus(str, Enum):
    """Job posting status."""

    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"
    ARCHIVED = "archived"


class JobSource(str, Enum):
    """Job source enumeration."""

    MANUAL = "manual"
    LINKEDIN = "linkedin"
    INDEED = "indeed"
    MONSTER = "monster"
    GREENHOUSE = "greenhouse"
    LEVER = "lever"
    OTHER = "other"


class Job(Base):
    """Job model for job listings."""

    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source: Mapped[str] = mapped_column(
        String(50),
        default=JobSource.MANUAL.value,
        nullable=False,
    )

    # Job details
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    company_logo: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    company_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    location: Mapped[str | None] = mapped_column(String(500), nullable=True)
    remote_policy: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Employment details
    employment_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    experience_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    salary_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_currency: Mapped[str] = mapped_column(String(10), default="USD")
    salary_visible: Mapped[bool] = mapped_column(Boolean, default=False)

    # Job content
    description: Mapped[str] = mapped_column(Text, nullable=False)
    requirements: Mapped[str | None] = mapped_column(Text, nullable=True)
    benefits: Mapped[str | None] = mapped_column(Text, nullable=True)
    skills: Mapped[list | None] = mapped_column(nullable=True)

    # URLs
    apply_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Status
    status: Mapped[str] = mapped_column(
        String(50),
        default=JobStatus.ACTIVE.value,
        nullable=False,
    )
    featured: Mapped[bool] = mapped_column(Boolean, default=False)

    # Caching
    cached_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    cache_ttl_hours: Mapped[int] = mapped_column(Integer, default=24)

    # Timestamps
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
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

    __table_args__ = (
        Index("ix_jobs_external_id", "external_id"),
        Index("ix_jobs_source", "source"),
        Index("ix_jobs_status", "status"),
        Index("ix_jobs_company_name", "company_name"),
        Index("ix_jobs_created_at", "created_at"),
        Index("ix_jobs_published_at", "published_at"),
        Index("ix_jobs_featured", "featured"),
    )

    def __repr__(self) -> str:
        return f"<Job(id={self.id}, title={self.title}, company={self.company_name})>"
