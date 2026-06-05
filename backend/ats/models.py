"""
Pydantic data models for ATS scoring system.

These models define the structured data representations for:
- Parsed resumes (extracted from PDF/DOCX)
- ATS scores and breakdowns
- Improvement suggestions
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


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


class ExperienceEntry(BaseModel):
    """A single work experience entry."""
    
    id: UUID = Field(default_factory=uuid4)
    company: str
    title: str
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    current: bool = False
    description: str
    skills_mentioned: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
    years_duration: Optional[float] = None
    
    @field_validator("years_duration", mode="before")
    @classmethod
    def calculate_duration(cls, v: Optional[float], info) -> Optional[float]:
        """Calculate years of experience from dates if not provided."""
        if v is not None:
            return v
        # This would be calculated by the parser based on dates
        return None


class EducationEntry(BaseModel):
    """A single education entry."""
    
    id: UUID = Field(default_factory=uuid4)
    institution: str
    degree: str
    field_of_study: Optional[str] = None
    graduation_date: Optional[str] = None
    gpa: Optional[str] = None
    honors: Optional[str] = None


class CertificationEntry(BaseModel):
    """A single certification entry."""
    
    id: UUID = Field(default_factory=uuid4)
    name: str
    issuer: Optional[str] = None
    date_obtained: Optional[str] = None
    expiration_date: Optional[str] = None
    credential_id: Optional[str] = None


class ResumeSection(BaseModel):
    """A section of a parsed resume."""
    
    section_type: SectionType
    raw_text: str
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence score for section parsing")
    parsed_data: Optional[dict] = None


class ParsedResume(BaseModel):
    """A fully parsed resume with extracted sections and data."""
    
    id: UUID = Field(default_factory=uuid4)
    filename: str
    file_type: str  # "pdf" or "docx"
    parsed_at: datetime = Field(default_factory=datetime.utcnow)
    raw_text: str
    sections: list[ResumeSection] = Field(default_factory=list)
    
    # Extracted structured data
    contact_info: Optional[dict] = None
    summary: Optional[str] = None
    experience: list[ExperienceEntry] = Field(default_factory=list)
    education: list[EducationEntry] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    certifications: list[CertificationEntry] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    
    # Metadata
    total_experience_years: Optional[float] = None
    education_level: Optional[str] = None
    skills_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    
    def get_all_text(self) -> str:
        """Get all text content from the resume."""
        parts = [self.raw_text]
        for section in self.sections:
            parts.append(section.raw_text)
        if self.summary:
            parts.append(self.summary)
        return "\n".join(parts)
    
    def get_experience_text(self) -> str:
        """Get combined experience descriptions."""
        return "\n".join(exp.description for exp in self.experience)
    
    def get_skills_normalized(self) -> set[str]:
        """Get normalized (lowercase, stripped) skills set."""
        return {skill.lower().strip() for skill in self.skills}


class JobDescription(BaseModel):
    """A job description to match resumes against."""
    
    id: UUID = Field(default_factory=uuid4)
    title: str
    company: Optional[str] = None
    raw_text: str
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    required_experience_years: Optional[float] = None
    required_education: Optional[str] = None
    keywords: list[str] = Field(default_factory=list)
    weight_map: dict[str, float] = Field(default_factory=dict)  # skill -> weight


class SectionScore(BaseModel):
    """Score for a specific resume section."""
    
    section_name: str
    score: float = Field(ge=0.0, le=100.0)
    max_score: float = Field(ge=0.0, le=100.0)
    percentage: float = Field(ge=0.0, le=100.0)
    details: dict = Field(default_factory=dict)


class ScoreBreakdown(BaseModel):
    """Detailed breakdown of the ATS score."""
    
    skills_match_score: float = Field(ge=0.0, le=100.0, description="Skills matching score")
    skills_match_details: dict = Field(default_factory=dict)
    
    keyword_relevance_score: float = Field(ge=0.0, le=100.0, description="TF-IDF keyword relevance")
    keyword_relevance_details: dict = Field(default_factory=dict)
    
    experience_match_score: float = Field(ge=0.0, le=100.0, description="Experience matching")
    experience_match_details: dict = Field(default_factory=dict)
    
    education_match_score: float = Field(ge=0.0, le=100.0, description="Education matching")
    education_match_details: dict = Field(default_factory=dict)
    
    format_score: float = Field(ge=0.0, le=100.0, description="Resume format/structure score")
    format_details: dict = Field(default_factory=dict)
    
    section_scores: list[SectionScore] = Field(default_factory=list)


class ImprovementSuggestion(BaseModel):
    """A suggestion for improving the resume."""
    
    id: UUID = Field(default_factory=uuid4)
    suggestion_type: SuggestionType
    severity: Severity
    title: str
    description: str
    current_value: Optional[str] = None
    suggested_value: Optional[str] = None
    location: Optional[str] = None  # Section or line reference
    impact_score: float = Field(ge=0.0, le=10.0, description="Estimated impact (0-10)")
    priority: int = Field(ge=1, le=5, description="Priority rank (1=highest)")
    
    def __lt__(self, other: ImprovementSuggestion) -> bool:
        """Sort by priority."""
        return self.priority < other.priority


class ATSScore(BaseModel):
    """Complete ATS scoring result for a resume against a job description."""
    
    id: UUID = Field(default_factory=uuid4)
    resume_id: UUID
    job_id: UUID
    scored_at: datetime = Field(default_factory=datetime.utcnow)
    
    overall_score: float = Field(ge=0.0, le=100.0)
    grade: str = Field(description="Letter grade (A, B, C, D, F)")
    percentile: float = Field(ge=0.0, le=100.0, description="Percentile ranking")
    
    breakdown: ScoreBreakdown
    suggestions: list[ImprovementSuggestion] = Field(default_factory=list)
    
    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    matched_keywords: list[str] = Field(default_factory=list)
    missing_keywords: list[str] = Field(default_factory=list)
    
    confidence: float = Field(ge=0.0, le=1.0, description="Score confidence level")
    explanation: str = Field(description="Human-readable explanation")
    
    @field_validator("grade", mode="before")
    @classmethod
    def calculate_grade(cls, v: Optional[str], info) -> str:
        """Calculate letter grade from overall score."""
        if v:
            return v
        # Get score from values
        data = info.data
        score = data.get("overall_score", 0)
        
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
    
    @field_validator("percentile", mode="before")
    @classmethod
    def calculate_percentile(cls, v: Optional[float], info) -> float:
        """Calculate percentile (placeholder - would need population data)."""
        if v is not None:
            return v
        data = info.data
        score = data.get("overall_score", 0)
        # Simplified percentile estimation
        return min(99.0, score)
