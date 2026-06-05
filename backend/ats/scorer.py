"""
ATS scoring engine — deterministic, explainable resume-to-job matching.

Why deterministic instead of LLM-based:
- Same input always produces the same score (auditable, testable)
- No GPU/API cost per score (suitable for high-volume scoring)
- Per-section breakdown explains the score to the user
- The score is a property of the resume and the job, not the LLM

Scoring approach:
1. TF-IDF cosine similarity on the full text (keyword relevance)
2. Weighted skill matching (synonym-aware)
3. Structural completeness heuristics (contact info, sections, length)
4. Education requirement matching
5. Final score: 0-100, weighted combination
6. Letter grade A-F + percentile estimate + human-readable explanation
"""

from __future__ import annotations

import re
import uuid
from typing import Iterable, Optional

try:
    from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore
    from sklearn.metrics.pairwise import cosine_similarity  # type: ignore
    _SKLEARN_AVAILABLE = True
except ImportError:
    _SKLEARN_AVAILABLE = False

from .models import (
    ATSScore,
    ImprovementSuggestion,
    ParsedResume,
    ScoreBreakdown,
    SectionScore,
    Severity,
    SuggestionType,
)


# ---------------------------------------------------------------------------
# Built-in skill synonym dictionary. Extend per-domain as needed.
# ---------------------------------------------------------------------------
SKILL_SYNONYMS: dict[str, set[str]] = {
    "javascript": {"js", "node.js", "nodejs", "es6", "ecmascript"},
    "typescript": {"ts"},
    "python": {"py", "python3", "python 3"},
    "java": {"jdk", "jre", "spring"},
    "react": {"reactjs", "react.js"},
    "vue": {"vuejs", "vue.js"},
    "angular": {"angularjs", "ng"},
    "aws": {"amazon web services", "ec2", "s3", "lambda", "rds"},
    "gcp": {"google cloud", "google cloud platform", "bigquery"},
    "azure": {"microsoft azure", "azure functions"},
    "docker": {"containers", "containerization"},
    "kubernetes": {"k8s"},
    "postgresql": {"postgres", "psql"},
    "mongodb": {"mongo"},
    "redis": {"key-value store"},
    "machine learning": {"ml"},
    "artificial intelligence": {"ai"},
    "natural language processing": {"nlp"},
    "computer vision": {"cv"},
    "rest api": {"restful", "rest", "rest api"},
    "graphql": {"graph ql"},
    "ci/cd": {"cicd", "continuous integration", "continuous deployment"},
    "terraform": {"tf", "iac"},
    "fastapi": {"fast api"},
    "django": {"django rest framework", "drf"},
    "flask": {},
    "pandas": {},
    "numpy": {},
    "pytorch": {},
    "tensorflow": {"tf"},
    "scikit-learn": {"sklearn"},
}


STOPWORDS = {
    "a", "an", "and", "or", "the", "of", "to", "in", "for", "with", "on",
    "as", "at", "by", "from", "is", "are", "was", "were", "be", "been",
    "experience", "work", "team", "company", "using", "knowledge",
}


WEAK_VERBS = {
    "helped", "assisted", "worked", "was responsible", "involved in",
    "participated", "contributed", "supported", "handled", "did",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _normalize_token(t: str) -> str:
    return re.sub(r"[^a-z0-9.+#-]", "", t.lower().strip())


def _expand_skill(skill: str) -> set[str]:
    s = skill.lower().strip()
    syns = SKILL_SYNONYMS.get(s, set())
    return {s, *syns}


def _grade_from_score(score: float) -> str:
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def _percentile_estimate(score: float) -> float:
    """Rough percentile estimate based on a normal distribution.
    Assumes a candidate pool with mean ~55, stddev ~15."""
    z = (score - 55) / 15
    return max(0.0, min(100.0, 50.0 * (1 + z / (1 + abs(z)))))


# ---------------------------------------------------------------------------
# Required-skill extraction from job descriptions
# ---------------------------------------------------------------------------
def extract_required_skills(job_text: str, max_skills: int = 30) -> list[str]:
    """Heuristically extract required skills from a job description."""
    explicit_pats = [
        r"(?:requirements?|must[- ]?have|required(?:\s+skills?)?|qualifications?)\s*[:\-]\s*(.+?)(?:\n\s*\n|\Z)",
        r"(?:nice[- ]?to[- ]?have|preferred|bonus)\s*[:\-]\s*(.+?)(?:\n\s*\n|\Z)",
    ]
    candidates: list[str] = []
    for pat in explicit_pats:
        for m in re.finditer(pat, job_text, re.IGNORECASE | re.DOTALL):
            block = m.group(1)
            for line in block.splitlines():
                line = line.strip(" \t-*•·")
                if not line:
                    continue
                for piece in re.split(r"[,;]|\band\b", line):
                    piece = piece.strip()
                    if 2 < len(piece) < 50:
                        candidates.append(piece)
    if candidates:
        return list(dict.fromkeys(candidates))[:max_skills]

    text_lower = job_text.lower()
    found: list[str] = []
    seen: set[str] = set()
    for canonical, syns in SKILL_SYNONYMS.items():
        forms = {canonical, *syns}
        for form in forms:
            if re.search(rf"\b{re.escape(form)}\b", text_lower):
                if canonical not in seen:
                    seen.add(canonical)
                    found.append(canonical)
                break
    return found[:max_skills]


# ---------------------------------------------------------------------------
# Skill matching
# ---------------------------------------------------------------------------
def _resume_skill_set(resume: ParsedResume) -> set[str]:
    out: set[str] = set()
    for s in resume.skills:
        s_norm = _normalize_token(s)
        if s_norm and s_norm not in STOPWORDS:
            out.add(s_norm)
    text = (resume.raw_text or "").lower()
    for canonical, syns in SKILL_SYNONYMS.items():
        forms = {canonical, *syns}
        for form in forms:
            if re.search(rf"\b{re.escape(form)}\b", text):
                out.add(canonical)
                break
    return out


def match_skills(
    resume: ParsedResume, required_skills: Iterable[str]
) -> tuple[set[str], set[str]]:
    resume_skills = _resume_skill_set(resume)
    required_set = {_normalize_token(s) for s in required_skills}
    matched: set[str] = set()
    missing: set[str] = set()
    for req in required_set:
        if not req or req in STOPWORDS:
            continue
        expanded = _expand_skill(req)
        if resume_skills & expanded:
            matched.add(req)
        else:
            missing.add(req)
    return matched, missing


# ---------------------------------------------------------------------------
# Component scorers — each returns 0-100
# ---------------------------------------------------------------------------
def _tfidf_score(resume: ParsedResume, job_text: str) -> int:
    """TF-IDF cosine similarity on the full text. 0-100."""
    if not _SKLEARN_AVAILABLE:
        return 0
    try:
        vec = TfidfVectorizer(stop_words="english", max_features=5000)
        docs = [resume.all_text or "", job_text or ""]
        if not any(d.strip() for d in docs):
            return 0
        tfidf = vec.fit_transform(docs)
        sim = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
        return max(0, min(100, int(round(sim * 100))))
    except Exception:
        return 0


def _skill_score(matched: set[str], required: set[str]) -> int:
    if not required:
        return 100
    rate = len(matched) / len(required)
    return max(0, min(100, int(round(rate * 100))))


def _structure_score(resume: ParsedResume) -> int:
    score = 0
    if resume.name:
        score += 15
    if resume.email:
        score += 15
    if resume.phone:
        score += 10
    if resume.summary:
        score += 15
    if resume.skills:
        score += 20
    if resume.experience:
        score += 15
    if resume.education:
        score += 10
    return min(100, score)


def _length_score(resume: ParsedResume) -> int:
    word_count = len((resume.raw_text or "").split())
    if word_count < 200:
        return max(0, int(word_count / 200 * 100))
    if word_count > 5000:
        return max(0, 100 - int((word_count - 5000) / 50))
    return 100


def _format_score(resume: ParsedResume) -> int:
    score = 0
    if resume.name and resume.email:
        score += 30
    if resume.summary:
        score += 20
    if resume.skills:
        score += 25
    if resume.experience:
        score += 25
    return min(100, score)


def _education_score(resume: ParsedResume, job_text: str) -> int:
    job_lower = job_text.lower()
    if "phd" in job_lower or "doctorate" in job_lower:
        target = "phd"
    elif "master" in job_lower or "ms " in job_lower or "msc" in job_lower:
        target = "master"
    elif "bachelor" in job_lower or "bs " in job_lower or "bsc" in job_lower or "undergraduate" in job_lower:
        target = "bachelor"
    else:
        return 100
    return 100 if resume.education else 0


# ---------------------------------------------------------------------------
# Suggestion generation
# ---------------------------------------------------------------------------
def _build_suggestions(
    resume: ParsedResume,
    missing_skills: set[str],
) -> list[ImprovementSuggestion]:
    suggestions: list[ImprovementSuggestion] = []

    for i, skill in enumerate(sorted(missing_skills)):
        suggestions.append(
            ImprovementSuggestion(
                type=SuggestionType.MISSING_KEYWORD,
                severity=Severity.HIGH,
                title=f"Add '{skill}' to your resume",
                message=(
                    f"The job description requires '{skill}'. "
                    f"Add it to your Skills section or work it into your "
                    f"experience bullets where applicable."
                ),
                location="skills",
                impact_score=8.0,
                priority=1 + i // 3,
            )
        )

    for entry in resume.experience:
        desc = (entry.description or "").lower()
        for weak in WEAK_VERBS:
            if weak in desc:
                suggestions.append(
                    ImprovementSuggestion(
                        type=SuggestionType.WEAK_VERB,
                        severity=Severity.MEDIUM,
                        title=f"Replace weak verb '{weak}'",
                        message=(
                            f"Use a stronger action verb (built, led, designed, "
                            f"shipped, optimized) instead of '{weak}'."
                        ),
                        current_value=weak,
                        location=f"experience:{entry.title}",
                        impact_score=4.0,
                        priority=2,
                    )
                )
                break

    for entry in resume.experience:
        desc = entry.description or ""
        if not re.search(r"\d+", desc):
            suggestions.append(
                ImprovementSuggestion(
                    type=SuggestionType.QUANTIFICATION,
                    severity=Severity.MEDIUM,
                    title=f"Add numbers to '{entry.title}'",
                    message=(
                        "Recruiters scan for quantified impact (%, $, count). "
                        "Add at least one metric to this experience entry."
                    ),
                    location=f"experience:{entry.title}",
                    impact_score=5.0,
                    priority=2,
                )
            )

    word_count = len((resume.raw_text or "").split())
    if word_count < 200:
        suggestions.append(
            ImprovementSuggestion(
                type=SuggestionType.LENGTH_ISSUE,
                severity=Severity.HIGH,
                title=f"Resume is too short ({word_count} words)",
                message="Aim for 400-800 words with detailed experience.",
                current_value=str(word_count),
                suggested_value="500-800",
                location="global",
                impact_score=7.0,
                priority=1,
            )
        )
    elif word_count > 1500:
        suggestions.append(
            ImprovementSuggestion(
                type=SuggestionType.LENGTH_ISSUE,
                severity=Severity.LOW,
                title=f"Resume is long ({word_count} words)",
                message="Consider trimming to 800-1000 words for most roles.",
                current_value=str(word_count),
                suggested_value="800-1000",
                location="global",
                impact_score=2.0,
                priority=3,
            )
        )

    if not resume.email:
        suggestions.append(
            ImprovementSuggestion(
                type=SuggestionType.FORMAT_ISSUE,
                severity=Severity.CRITICAL,
                title="No email address detected",
                message="Add your email to the contact section.",
                location="contact",
                impact_score=10.0,
                priority=1,
            )
        )

    suggestions.sort()
    return suggestions


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------
def score_against_job(
    resume: ParsedResume,
    job_text: str,
    weights: Optional[dict[str, float]] = None,
    resume_id: Optional[uuid.UUID] = None,
    job_id: Optional[uuid.UUID] = None,
) -> ATSScore:
    """Score a parsed resume against a job description.

    Returns an ATSScore:
    - score (0-100), grade (A-F), percentile (rough estimate)
    - breakdown (per-component scores)
    - matched_skills / missing_skills
    - suggestions (sorted by priority)
    - confidence + explanation
    """
    if weights is None:
        weights = {
            "tfidf": 0.30,
            "skills": 0.35,
            "structure": 0.15,
            "length": 0.05,
            "format": 0.10,
            "education": 0.05,
        }

    required_skills = extract_required_skills(job_text)
    matched, missing = match_skills(resume, required_skills)

    tfidf = _tfidf_score(resume, job_text)
    skills = _skill_score(matched, set(required_skills))
    structure = _structure_score(resume)
    length = _length_score(resume)
    fmt = _format_score(resume)
    education = _education_score(resume, job_text)

    overall = (
        tfidf * weights.get("tfidf", 0.30)
        + skills * weights.get("skills", 0.35)
        + structure * weights.get("structure", 0.15)
        + length * weights.get("length", 0.05)
        + fmt * weights.get("format", 0.10)
        + education * weights.get("education", 0.05)
    )
    overall_score = max(0.0, min(100.0, round(overall, 2)))

    section_scores = [
        SectionScore(section_name="skills_match", score=float(skills), percentage=float(skills)),
        SectionScore(section_name="keyword_relevance", score=float(tfidf), percentage=float(tfidf)),
        SectionScore(section_name="format", score=float(fmt), percentage=float(fmt)),
        SectionScore(section_name="length", score=float(length), percentage=float(length)),
    ]

    breakdown = ScoreBreakdown(
        tfidf=float(tfidf),
        skills=float(skills),
        structure=float(structure),
        length=float(length),
        format=float(fmt),
        education=float(education),
        section_scores=section_scores,
    )

    suggestions = _build_suggestions(resume, missing)

    explanation = (
        f"Resume scored {overall_score:.0f}/100 (Grade {_grade_from_score(overall_score)}) "
        f"based on {len(required_skills)} required skills, with "
        f"{len(matched)} matched and {len(missing)} missing. "
        f"Keyword relevance: {tfidf}%, skills match: {skills}%, "
        f"format: {fmt}%. "
        f"{'Strong candidate — apply with confidence.' if overall_score >= 75 else 'Consider improving the suggestions below before applying.'}"
    )

    confidence = min(1.0, len(required_skills) / 10) if required_skills else 0.5

    return ATSScore(
        resume_id=resume_id or uuid.uuid4(),
        job_id=job_id or uuid.uuid4(),
        score=overall_score,
        grade=_grade_from_score(overall_score),
        percentile=_percentile_estimate(overall_score),
        breakdown=breakdown,
        suggestions=suggestions,
        matched_skills=sorted(matched),
        missing_skills=sorted(missing),
        matched_keywords=sorted(matched),
        missing_keywords=sorted(missing),
        confidence=round(confidence, 2),
        explanation=explanation,
    )
