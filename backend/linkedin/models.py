"""
LinkedIn Profile Optimizer — Pydantic data models.

Lean schema: just enough for parse → score → rewrite.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class SuggestionType(str, Enum):
    HEADLINE = "headline"
    ABOUT = "about"
    EXPERIENCE = "experience"
    SKILLS = "skills"
    COMPLETENESS = "completeness"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


# ---------------------------------------------------------------------------
# Profile components
# ---------------------------------------------------------------------------
class LinkedInSection(BaseModel):
    """A single section of a LinkedIn profile (e.g. one experience role)."""
    title: str
    body: str


class LinkedInProfile(BaseModel):
    """A parsed LinkedIn profile."""
    id: UUID = Field(default_factory=uuid4)
    headline: str = ""
    about: str = ""
    experience: list[LinkedInSection] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    raw_text: str = ""
    parsed_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def all_text(self) -> str:
        parts = [self.headline, self.about, self.raw_text]
        return "\n".join(p for p in parts if p)


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------
class ProfileScore(BaseModel):
    """Per-section + overall profile score."""
    overall: float = Field(ge=0.0, le=100.0)
    headline: int = Field(ge=0, le=100)
    about: int = Field(ge=0, le=100)
    experience: int = Field(ge=0, le=100)
    skills: int = Field(ge=0, le=100)
    completeness: int = Field(ge=0, le=100)


class ProfileSuggestion(BaseModel):
    """A single actionable suggestion for improving the profile."""
    id: UUID = Field(default_factory=uuid4)
    type: SuggestionType
    severity: Severity
    title: str
    message: str
    current_value: Optional[str] = None
    suggested_value: Optional[str] = None
    location: Optional[str] = None


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
class OptimizationReport(BaseModel):
    """Complete optimization report for a LinkedIn profile."""
    id: UUID = Field(default_factory=uuid4)
    profile: LinkedInProfile
    score: ProfileScore
    suggestions: list[ProfileSuggestion] = Field(default_factory=list)
    headline_rewrites: list[str] = Field(default_factory=list)
    about_rewrite: str = ""
    bullet_rewrites: list[str] = Field(default_factory=list)
    target_role: str = ""
    generated_at: datetime = Field(default_factory=datetime.utcnow)
