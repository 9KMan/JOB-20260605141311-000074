"""
AI Resume Parsing + ATS Score Engine

This package provides deterministic ATS (Applicant Tracking System) scoring
capabilities for resume evaluation against job descriptions.
"""

__version__ = "0.1.0"

from backend.ats.parser import ResumeParser
from backend.ats.scorer import ATSScorer
from backend.ats.suggestions import SuggestionGenerator
from backend.ats.models import (
    ParsedResume,
    ResumeSection,
    ATSScore,
    SectionScore,
    ScoreBreakdown,
    ImprovementSuggestion,
    SuggestionType,
    Severity,
)

__all__ = [
    "ResumeParser",
    "ATSScorer",
    "SuggestionGenerator",
    "ParsedResume",
    "ResumeSection",
    "ATSScore",
    "SectionScore",
    "ScoreBreakdown",
    "ImprovementSuggestion",
    "SuggestionType",
    "Severity",
]
