"""
AI Resume Parsing + ATS Score Engine

This package provides deterministic ATS (Applicant Tracking System) scoring
capabilities for resume evaluation against job descriptions.

Public API:
    parse_resume(path)        - Parse a resume file (PDF/DOCX/text)
    parse_resume_text(text)   - Parse resume from raw text
    score_against_job(resume, job_text)  - Score a parsed resume vs a job
    extract_required_skills(job_text)    - Extract required skills from a job
    match_skills(resume, required)       - Match resume skills to required

Design choice: deterministic scoring (TF-IDF + weighted skill matching).
No LLM dependency for the score itself — auditable, reproducible, no API cost.
"""

__version__ = "0.1.0"

from .parser import parse_resume, parse_resume_text
from .scorer import (
    score_against_job,
    extract_required_skills,
    match_skills,
    SKILL_SYNONYMS,
)
from .models import (
    ATSScore,
    EducationEntry,
    ExperienceEntry,
    ImprovementSuggestion,
    JobDescription,
    ParsedResume,
    ScoreBreakdown,
    SectionScore,
    SectionType,
    Severity,
    SuggestionType,
)

__all__ = [
    "parse_resume",
    "parse_resume_text",
    "score_against_job",
    "extract_required_skills",
    "match_skills",
    "SKILL_SYNONYMS",
    "ATSScore",
    "EducationEntry",
    "ExperienceEntry",
    "ImprovementSuggestion",
    "JobDescription",
    "ParsedResume",
    "ScoreBreakdown",
    "SectionScore",
    "SectionType",
    "Severity",
    "SuggestionType",
]
