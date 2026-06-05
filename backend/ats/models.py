"""
Pydantic data models for the ATS scoring system.

These models define the structured data representations for:
- Parsed resumes (extracted from PDF/DOCX/text)
- ATS scores and breakdowns
- Improvement suggestions

Schema is intentionally lean — just enough for the deterministic scoring
engine (see scorer.py) to do its work. No LLM dependency.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------
class SectionType(str, Enum):
    """Types of resume sections."""
    CONTACT = "contact"
    SUMMARY = "summary"
    EXPERIENCE = "experience"
    EDUCATION = "education"
    SKILLS = "skills"
    CERTIFICATIONS = "certifications"
    PROJECTS = "projects"
    LANGUAGES = "languages"
    INTERESTS = "interests"
    REFERENCES = "references"
    UNKNOWN = "unknown"


class SuggestionType(str, Enum):
    """Types of improvement suggestions."""
    MISSING_KEYWORD = "missing_keyword"
    WEAK_VERB = "weak_verb"
    LENGTH_ISSUE = "length_issue"
    FORMAT_ISSUE = "format_issue"
    SKILL_GAP = "skill_gap"
    QUANTIFICATION = "quantification"
    KEYWORD_DENSITY = "keyword_density"


class Severity(str, Enum):
    """Severity levels for suggestions."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


# ---------------------------------------------------------------------------
# Resume components
# ---------------------------------------------------------------------------
class ExperienceEntry(BaseModel):
    """A single work experience entry."""
    title: str
    company: str = ""
    location: Optional[str] = None
    start: Optional[str] = None  # free-form: "2020", "Jan 2020"
    end: Optional[str] = None    # free-form: "2023", "Present"
    description: str = ""
    skills_mentioned: list[str] = Field(default_factory=list)


class EducationEntry(BaseModel):
    """A single education entry."""
    institution: str
    degree: str = ""
    field_of_study: Optional[str] = None
    graduation_date: Optional[str] = None


class CertificationEntry(BaseModel):
    """A single certification entry."""
    name: str
    issuer: Optional[str] = None
    date_obtained: Optional[str] = None


# ---------------------------------------------------------------------------
# ParsedResume
# ---------------------------------------------------------------------------
class ParsedResume(BaseModel):
    """A fully parsed resume with extracted structured data."""
    id: UUID = Field(default_factory=uuid4)
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    summary: Optional[str] = None
    skills: list[str] = Field(default_factory=list)
    experience: list[ExperienceEntry] = Field(default_factory=list)
    education: list[EducationEntry] = Field(default_factory=list)
    certifications: list[CertificationEntry] = Field(default_factory=list)
    raw_text: str = ""
    parsed_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def all_text(self) -> str:
        """All text content from the resume (raw + summary)."""
        parts = [self.raw_text or ""]
        if self.summary:
            parts.append(self.summary)
        return "\n".join(parts)

    @property
    def skills_normalized(self) -> set[str]:
        """Lowercased, stripped skills set."""
        return {s.lower().strip() for s in self.skills}


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------
class SectionScore(BaseModel):
    """Score for a specific scoring component."""
    section_name: str
    score: float = Field(ge=0.0, le=100.0)
    max_score: float = Field(ge=0.0, le=100.0, default=100.0)
    percentage: float = Field(ge=0.0, le=100.0)


class ScoreBreakdown(BaseModel):
    """Detailed breakdown of the ATS score."""
    tfidf: float = Field(ge=0.0, le=100.0, description="TF-IDF cosine similarity")
    skills: float = Field(ge=0.0, le=100.0, description="Skill match rate")
    structure: float = Field(ge=0.0, le=100.0, description="Structural completeness")
    length: float = Field(ge=0.0, le=100.0, description="Resume length heuristic")
    format: float = Field(ge=0.0, le=100.0, description="Format/contact info")
    education: float = Field(ge=0.0, le=100.0, description="Education requirement match")
    section_scores: list[SectionScore] = Field(default_factory=list)


class ImprovementSuggestion(BaseModel):
    """A single actionable improvement suggestion."""
    id: UUID = Field(default_factory=uuid4)
    type: SuggestionType
    severity: Severity
    title: str
    message: str
    location: Optional[str] = None
    current_value: Optional[str] = None
    suggested_value: Optional[str] = None
    impact_score: float = Field(ge=0.0, le=10.0, default=5.0)
    priority: int = Field(ge=1, le=5, default=3)

    def __lt__(self, other: "ImprovementSuggestion") -> bool:
        return self.priority < other.priority


class ATSScore(BaseModel):
    """Complete ATS scoring result for a resume against a job description."""
    id: UUID = Field(default_factory=uuid4)
    resume_id: Optional[UUID] = None
    job_id: Optional[UUID] = None
    scored_at: datetime = Field(default_factory=datetime.utcnow)

    score: float = Field(ge=0.0, le=100.0, description="Overall score 0-100")
    grade: str = Field(description="Letter grade A-F")
    percentile: float = Field(ge=0.0, le=100.0, description="Rough percentile estimate")

    breakdown: ScoreBreakdown
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    matched_keywords: list[str] = Field(default_factory=list)
    missing_keywords: list[str] = Field(default_factory=list)

    suggestions: list[ImprovementSuggestion] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    explanation: str = ""


class JobDescription(BaseModel):
    """A structured job description."""
    id: UUID = Field(default_factory=uuid4)
    title: str
    company: Optional[str] = None
    description: str
    required_skills: list[str] = Field(default_factory=list)
    nice_to_have: list[str] = Field(default_factory=list)
