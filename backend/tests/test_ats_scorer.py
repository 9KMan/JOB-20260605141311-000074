"""
Smoke tests for the ATS scoring engine.

Run with:
    cd backend && python3 -m pytest tests/test_ats_scorer.py -v
or directly:
    cd backend && python3 tests/test_ats_scorer.py
"""

import sys
from pathlib import Path

# Allow running this file directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from ats import (
    parse_resume_text,
    score_against_job,
    extract_required_skills,
    match_skills,
    SKILL_SYNONYMS,
)


SAMPLE_RESUME = """
John Doe
john.doe@example.com | +1-555-123-4567

Summary
Senior Python engineer with 8 years of experience building scalable web
applications. Expert in PostgreSQL, AWS, Docker, and REST API design.

Experience
Senior Engineer | Acme Corp
2020 - Present
Built a real-time analytics platform serving 10M requests/day.
Led migration from MySQL to PostgreSQL, reducing query time by 60%.

Engineer | Beta Inc
2017 - 2020
Designed REST APIs for mobile clients serving 500K MAU.

Education
BS Computer Science | MIT | 2017

Skills
Python, FastAPI, PostgreSQL, AWS, Docker, Kubernetes, REST API
"""

SAMPLE_JOB = """
Senior Backend Engineer

Requirements:
- Python (5+ years)
- PostgreSQL
- AWS (EC2, Lambda, S3)
- Docker / Kubernetes
- REST API design
- FastAPI or Django
"""


def test_parse_resume_text():
    resume = parse_resume_text(SAMPLE_RESUME)
    assert resume.name == "John Doe"
    assert resume.email == "john.doe@example.com"
    assert "Python" in resume.skills
    assert "PostgreSQL" in resume.skills
    assert len(resume.experience) >= 1
    assert len(resume.education) >= 1
    print("✓ test_parse_resume_text passed")


def test_extract_required_skills():
    skills = extract_required_skills(SAMPLE_JOB)
    assert len(skills) > 0
    # Python, PostgreSQL, AWS, Docker, Kubernetes, REST should all be in the list
    skills_lower = [s.lower() for s in skills]
    assert any("python" in s for s in skills_lower), f"Python missing from {skills}"
    print(f"✓ test_extract_required_skills passed (found {len(skills)} skills: {skills[:5]}...)")


def test_match_skills():
    resume = parse_resume_text(SAMPLE_RESUME)
    required = ["Python", "PostgreSQL", "Rust", "COBOL"]
    matched, missing = match_skills(resume, required)
    assert "python" in matched
    assert "postgresql" in matched
    assert "rust" in missing
    assert "cobol" in missing
    print(f"✓ test_match_skills passed (matched={matched}, missing={missing})")


def test_skill_synonyms():
    """Resume says 'postgres' should match requirement 'PostgreSQL'."""
    resume_text = """
Jane Smith
jane@example.com

Skills
postgres, react, k8s
"""
    resume = parse_resume_text(resume_text)
    required = ["PostgreSQL", "React", "Kubernetes"]
    matched, missing = match_skills(resume, required)
    assert "postgresql" in matched, f"postgres should match PostgreSQL: matched={matched}"
    assert "react" in matched
    assert "kubernetes" in matched
    assert len(missing) == 0
    print(f"✓ test_skill_synonyms passed (matched={matched})")


def test_score_against_job():
    resume = parse_resume_text(SAMPLE_RESUME)
    score = score_against_job(resume, SAMPLE_JOB)
    assert 0 <= score.score <= 100
    assert score.grade in ["A", "B", "C", "D", "F"]
    assert 0 <= score.percentile <= 100
    assert score.confidence > 0
    assert len(score.explanation) > 20
    print(f"✓ test_score_against_job passed (score={score.score}, grade={score.grade}, matched={len(score.matched_skills)})")


def test_empty_job_text():
    """An empty job description should still produce a score (just lower)."""
    resume = parse_resume_text(SAMPLE_RESUME)
    score = score_against_job(resume, "")
    assert 0 <= score.score <= 100
    # With no requirements, skills component should be 100
    assert score.breakdown.skills == 100.0
    print(f"✓ test_empty_job_text passed (score={score.score})")


def test_weak_verb_detection():
    """Resume using 'helped' should trigger a WEAK_VERB suggestion."""
    resume_text = """
Bob
bob@example.com

Experience
Engineer | Co
2020 - 2024
Helped the team with various tasks.
"""
    resume = parse_resume_text(resume_text)
    job = "Engineer"
    score = score_against_job(resume, job)
    types = [s.type.value for s in score.suggestions]
    assert "weak_verb" in types, f"No weak_verb suggestion: types={types}"
    print("✓ test_weak_verb_detection passed")


def test_no_email_critical():
    """A resume with no email should produce a CRITICAL format_issue suggestion."""
    resume_text = """
Anonymous Candidate

Experience
Engineer | Co
2020 - 2024
Built stuff.
"""
    resume = parse_resume_text(resume_text)
    score = score_against_job(resume, "Engineer")
    critical = [s for s in score.suggestions if s.severity.value == "critical"]
    assert len(critical) > 0
    assert any("email" in s.title.lower() for s in critical)
    print("✓ test_no_email_critical passed")


if __name__ == "__main__":
    test_parse_resume_text()
    test_extract_required_skills()
    test_match_skills()
    test_skill_synonyms()
    test_score_against_job()
    test_empty_job_text()
    test_weak_verb_detection()
    test_no_email_critical()
    print(f"\n✓ All 8 tests passed. SKILL_SYNONYMS has {len(SKILL_SYNONYMS)} skill families.")
