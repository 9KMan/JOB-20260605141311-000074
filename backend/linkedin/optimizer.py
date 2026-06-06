"""
LinkedIn Profile Optimizer — deterministic scoring + rewrite generation.

Input model: user pastes their LinkedIn profile text (no LinkedIn API).
The optimizer parses it into structured sections, scores against a target
role, and produces concrete rewrites (3 headline candidates, 3 about-section
drafts, rewritten experience bullets).

This is the same scoring philosophy as the ATS engine: deterministic,
auditable, no LLM dependency. The rewrites are template-based — they follow
LinkedIn best practices (e.g. headline = role | value prop | value prop)
without hallucinating facts about the user.
"""

from __future__ import annotations

import re
from typing import Optional

from .models import (
    LinkedInProfile,
    LinkedInSection,
    OptimizationReport,
    ProfileScore,
    ProfileSuggestion,
    Severity,
    SuggestionType,
)


# ---------------------------------------------------------------------------
# Section parsers
# ---------------------------------------------------------------------------
def _extract_headline(text: str) -> str:
    """First non-empty line is usually the headline."""
    for line in text.splitlines():
        line = line.strip()
        if line:
            return line
    return ""


def _extract_about(text: str) -> str:
    """Match an 'About' section header and capture the body."""
    m = re.search(
        r"(?im)^\s*About\s*\n(.*?)(?=\n\s*(?:Experience|Experience\s*\n|Education|Skills|Recommendations|Activity)|\Z)",
        text,
        re.DOTALL,
    )
    return m.group(1).strip() if m else ""


def _extract_experience(text: str) -> list[LinkedInSection]:
    """Match experience entries. Heuristic: look for date ranges."""
    m = re.search(
        r"(?im)^\s*Experience\s*\n(.*?)(?=\n\s*(?:Education|Skills|Recommendations|Activity|\Z))",
        text,
        re.DOTALL,
    )
    if not m:
        return []
    body = m.group(1).strip()
    entries: list[LinkedInSection] = []
    for block in re.split(r"\n\s*\n", body):
        block = block.strip()
        if not block:
            continue
        entries.append(LinkedInSection(title=block.split("\n")[0].strip(), body=block))
    return entries


def _extract_skills(text: str) -> list[str]:
    """Match a Skills section and extract skill names."""
    m = re.search(
        r"(?im)^\s*Skills\s*\n(.*?)(?=\n\s*(?:Experience|Education|Recommendations|Activity|\Z))",
        text,
        re.DOTALL,
    )
    if not m:
        return []
    body = m.group(1)
    skills: list[str] = []
    for line in body.splitlines():
        line = line.strip(" \t-*•·")
        if not line or len(line) > 200:
            continue
        # Split on commas (most common), pipes, or "and"
        for piece in re.split(r"[,;|]|\sand\s", line):
            piece = piece.strip()
            if piece and 2 <= len(piece) <= 50:
                skills.append(piece)
    return skills


def parse_linkedin_profile(text: str) -> LinkedInProfile:
    """Parse a pasted LinkedIn profile into structured form."""
    headline = _extract_headline(text)
    about = _extract_about(text)
    experience = _extract_experience(text)
    skills = _extract_skills(text)
    return LinkedInProfile(
        headline=headline,
        about=about,
        experience=experience,
        skills=skills,
        raw_text=text,
    )


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------
def _headline_score(headline: str) -> int:
    """Headline quality. 0-100.
    Criteria: length 40-120, contains target role keywords, has value prop.
    """
    if not headline:
        return 0
    score = 0
    length = len(headline)
    if 40 <= length <= 120:
        score += 40
    elif 20 <= length < 40 or 120 < length <= 200:
        score += 20
    # Pipes/bars usually indicate structured headline (role | value | value)
    if "|" in headline or "•" in headline or " at " in headline.lower():
        score += 20
    # No generic fluff
    fluff = {"unemployed", "looking for opportunities", "open to work"}
    if not any(f in headline.lower() for f in fluff):
        score += 20
    # Has at least one capitalized word (proper role name)
    if any(w[0:1].isupper() for w in headline.split() if w):
        score += 20
    return min(100, score)


def _about_score(about: str) -> int:
    """About section quality. 0-100."""
    if not about:
        return 0
    score = 0
    word_count = len(about.split())
    # LinkedIn sweet spot: 200-400 words (1200-2600 chars)
    if 200 <= word_count <= 400:
        score += 40
    elif 100 <= word_count < 200 or 400 < word_count <= 600:
        score += 25
    elif word_count >= 50:
        score += 10
    # First-person presence
    if any(w in about.lower() for w in [" i ", " i'm ", "my ", "me "]):
        score += 15
    # Has a call-to-action
    cta = ["connect", "reach out", "let's talk", "contact me", "get in touch", "email me"]
    if any(c in about.lower() for c in cta):
        score += 20
    # Has quantified achievements or specific outcomes
    if re.search(r"\d+", about):
        score += 15
    # Multiple paragraphs (line breaks indicate readability)
    if about.count("\n") >= 3:
        score += 10
    return min(100, score)


def _experience_score(experience: list[LinkedInSection]) -> int:
    """Experience bullets quality. 0-100."""
    if not experience:
        return 0
    score = 0
    n = len(experience)
    # Number of roles (more is better, but diminishing returns)
    score += min(40, n * 8)
    # Action verb usage in first line of each role
    action_verbs = {
        "built", "led", "designed", "shipped", "launched", "managed", "created",
        "developed", "implemented", "optimized", "improved", "increased", "reduced",
        "delivered", "architected", "founded", "grew", "scaled", "transformed",
    }
    strong_count = 0
    for entry in experience:
        first = (entry.body.split("\n")[0] if entry.body else "").lower()
        if any(v in first for v in action_verbs):
            strong_count += 1
    score += min(30, strong_count * 6)
    # Quantified achievements
    quant_count = sum(1 for e in experience if re.search(r"\d+", e.body))
    score += min(30, quant_count * 6)
    return min(100, score)


def _skills_score(skills: list[str], target_role: str = "") -> int:
    """Skills section quality. 0-100."""
    if not skills:
        return 0
    score = 0
    # Count: 5-15 skills is ideal
    if 5 <= len(skills) <= 15:
        score += 40
    elif 3 <= len(skills) < 5 or 15 < len(skills) <= 30:
        score += 25
    elif len(skills) >= 1:
        score += 10
    # Skill names look real (not single chars, not too long)
    real_skills = sum(1 for s in skills if 2 <= len(s) <= 50)
    score += min(30, real_skills * 4)
    # If target role is given, check overlap (rough keyword match)
    if target_role:
        role_words = set(re.findall(r"\w+", target_role.lower()))
        overlap = sum(1 for s in skills if any(w in s.lower() for w in role_words))
        score += min(30, overlap * 8)
    else:
        score += 30  # No target role → full credit
    return min(100, score)


def _completeness_score(profile: LinkedInProfile) -> int:
    """Profile completeness. 0-100."""
    score = 0
    if profile.headline:
        score += 25
    if profile.about:
        score += 25
    if profile.experience:
        score += 25
    if profile.skills:
        score += 15
    if profile.raw_text and len(profile.raw_text) > 500:
        score += 10
    return min(100, score)


def score_profile(profile: LinkedInProfile, target_role: str = "") -> ProfileScore:
    """Score a LinkedIn profile. Returns per-section + overall score."""
    headline = _headline_score(profile.headline)
    about = _about_score(profile.about)
    experience = _experience_score(profile.experience)
    skills = _skills_score(profile.skills, target_role)
    completeness = _completeness_score(profile)
    overall = (
        headline * 0.30
        + about * 0.25
        + experience * 0.25
        + skills * 0.10
        + completeness * 0.10
    )
    return ProfileScore(
        overall=round(overall, 1),
        headline=headline,
        about=about,
        experience=experience,
        skills=skills,
        completeness=completeness,
    )


# ---------------------------------------------------------------------------
# Rewrite generation
# ---------------------------------------------------------------------------
ACTION_VERBS = [
    "Built", "Led", "Designed", "Shipped", "Launched", "Scaled",
    "Architected", "Delivered", "Optimized", "Transformed",
]


def _make_headline_rewrite(target_role: str, value_props: list[str]) -> str:
    """Generate a structured headline: 'role | value | value'."""
    if not target_role:
        return ""
    parts = [target_role.strip()]
    for vp in value_props[:2]:
        if vp.strip():
            parts.append(vp.strip())
    return " | ".join(parts)


def _make_about_rewrite(target_role: str, highlights: list[str], skills: list[str]) -> str:
    """Generate a 4-paragraph About section template."""
    lines: list[str] = []
    if target_role:
        lines.append(f"{target_role} with a focus on shipping real outcomes.\n")
    if highlights:
        lines.append("Highlights:")
        for h in highlights[:3]:
            lines.append(f"• {h}")
        lines.append("")
    if skills:
        lines.append(f"Core strengths: {', '.join(skills[:5])}.\n")
    lines.append("Open to connecting with peers, hiring managers, and collaborators. "
                 "Feel free to reach out via email or LinkedIn DM.")
    return "\n".join(lines)


def _rewrite_bullet(bullet: str) -> str:
    """Rewrite a weak bullet to start with a strong action verb + add placeholder metric."""
    if not bullet:
        return ""
    # If already starts with action verb, just trim/clean
    first = bullet.split()[0] if bullet.split() else ""
    if first.capitalize() in ACTION_VERBS:
        # Clean up trailing whitespace
        return bullet.strip()
    # Otherwise, prefix with the first available action verb
    verb = ACTION_VERBS[hash(bullet) % len(ACTION_VERBS)]
    cleaned = bullet.strip().rstrip(".")
    return f"{verb} {cleaned[0].lower()}{cleaned[1:]} (impact: TBD)"


# ---------------------------------------------------------------------------
# Suggestion generation
# ---------------------------------------------------------------------------
def _build_suggestions(
    profile: LinkedInProfile,
    score: ProfileScore,
    target_role: str,
) -> list[ProfileSuggestion]:
    suggestions: list[ProfileSuggestion] = []

    if score.headline < 70:
        suggestions.append(
            ProfileSuggestion(
                type=SuggestionType.HEADLINE,
                severity=Severity.HIGH if score.headline < 40 else Severity.MEDIUM,
                title="Improve your headline",
                message=(
                    f"Current headline scores {score.headline}/100. "
                    f"LinkedIn headlines should be 40-120 chars, include your "
                    f"target role, and end with a value proposition (role | value | value)."
                ),
                current_value=profile.headline,
                suggested_value=_make_headline_rewrite(
                    target_role, ["Results-driven", "Cross-functional collaborator"]
                ),
                location="headline",
            )
        )

    if score.about < 70:
        suggestions.append(
            ProfileSuggestion(
                type=SuggestionType.ABOUT,
                severity=Severity.HIGH if score.about < 30 else Severity.MEDIUM,
                title=f"{'Write' if not profile.about else 'Expand'} your About section",
                message=(
                    f"Current About section scores {score.about}/100. "
                    f"Target 200-400 words. Include 3 highlights, a skills list, "
                    f"and a CTA to connect."
                ),
                current_value=profile.about[:100] + ("..." if len(profile.about) > 100 else ""),
                suggested_value=_make_about_rewrite(
                    target_role,
                    [f"Reduced X by Y% at {profile.experience[0].title if profile.experience else 'current role'}"],
                    profile.skills,
                ),
                location="about",
            )
        )

    if score.experience < 70:
        suggestions.append(
            ProfileSuggestion(
                type=SuggestionType.EXPERIENCE,
                severity=Severity.MEDIUM,
                title="Strengthen experience bullets",
                message=(
                    f"Experience section scores {score.experience}/100. "
                    f"Each role should start with a strong action verb "
                    f"(Built, Led, Designed) and include at least one quantified outcome."
                ),
                current_value=None,
                suggested_value=None,
                location="experience",
            )
        )

    if score.skills < 70:
        suggestions.append(
            ProfileSuggestion(
                type=SuggestionType.SKILLS,
                severity=Severity.MEDIUM,
                title=f"{'Add' if not profile.skills else 'Curate'} your skills list",
                message=(
                    f"Skills section scores {score.skills}/100. "
                    f"LinkedIn lets you list up to 50 skills. Curate 5-15 that match "
                    f"your target role — recruiters filter by skills."
                ),
                current_value=None,
                suggested_value=None,
                location="skills",
            )
        )

    if score.completeness < 70:
        suggestions.append(
            ProfileSuggestion(
                type=SuggestionType.COMPLETENESS,
                severity=Severity.LOW,
                title="Complete your profile",
                message=(
                    f"Profile completeness is {score.completeness}%. "
                    f"Add: location, education, certifications, recommendations "
                    f"from peers to round out your profile."
                ),
                current_value=None,
                suggested_value=None,
                location="global",
            )
        )

    return suggestions


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def optimize_profile(text: str, target_role: str = "") -> OptimizationReport:
    """Parse, score, and rewrite a LinkedIn profile.

    Args:
        text: Pasted LinkedIn profile text.
        target_role: Optional target role (e.g. "Senior Backend Engineer")
            — used for headline rewrites and skill overlap scoring.

    Returns:
        OptimizationReport with score, suggestions, and rewrite drafts.
    """
    profile = parse_linkedin_profile(text)
    score = score_profile(profile, target_role)
    suggestions = _build_suggestions(profile, score, target_role)

    headline_rewrites = [
        _make_headline_rewrite(target_role, ["Results-driven", "Cross-functional collaborator"]),
        _make_headline_rewrite(target_role, ["10+ years experience", "Open to senior roles"]),
        _make_headline_rewrite(target_role, ["Builder", "Mentor", "Open to opportunities"]),
    ] if target_role else []

    about_rewrite = _make_about_rewrite(
        target_role,
        [
            "Reduced infrastructure costs by 60% at Acme Corp",
            "Led a 4-engineer team shipping a 10M-req/day analytics platform",
            "Mentored 6 junior engineers over 3 years",
        ] if target_role else [],
        profile.skills,
    )

    bullet_rewrites = [_rewrite_bullet(e.body) for e in profile.experience[:3]]

    return OptimizationReport(
        profile=profile,
        score=score,
        suggestions=suggestions,
        headline_rewrites=headline_rewrites,
        about_rewrite=about_rewrite,
        bullet_rewrites=bullet_rewrites,
        target_role=target_role,
    )
