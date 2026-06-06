"""
LinkedIn Profile Optimizer — deterministic scoring + rewrites.

Public API:
    parse_linkedin_profile(text)        - Parse pasted profile text
    score_profile(profile, target_role) - Score a parsed profile
    optimize_profile(text, target_role) - Full report (parse + score + rewrites)
"""

__version__ = "0.1.0"

from .models import (
    LinkedInProfile,
    LinkedInSection,
    OptimizationReport,
    ProfileScore,
    ProfileSuggestion,
    Severity,
    SuggestionType,
)
from .optimizer import (
    parse_linkedin_profile,
    score_profile,
    optimize_profile,
    ACTION_VERBS,
)

__all__ = [
    "parse_linkedin_profile",
    "score_profile",
    "optimize_profile",
    "ACTION_VERBS",
    "LinkedInProfile",
    "LinkedInSection",
    "OptimizationReport",
    "ProfileScore",
    "ProfileSuggestion",
    "Severity",
    "SuggestionType",
]
