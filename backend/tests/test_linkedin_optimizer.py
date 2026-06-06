"""
Smoke tests for the LinkedIn Profile Optimizer.

Run with:
    cd backend && PYTHONPATH=/tmp/poctest/lib/python3.11/site-packages:. python3 tests/test_linkedin_optimizer.py
or (with sklearn installed locally):
    cd backend && python3 -m pytest tests/test_linkedin_optimizer.py -v
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from linkedin import (
    optimize_profile,
    parse_linkedin_profile,
    score_profile,
    ACTION_VERBS,
)


SAMPLE_PROFILE = """
Senior Backend Engineer | Python, AWS, Distributed Systems

About
Senior Backend Engineer with 8 years of experience building scalable web
applications and APIs. Expert in Python, PostgreSQL, AWS, Docker, and REST
API design. Passionate about clean code, observability, and shipping
reliable systems.

Highlights:
• Built a real-time analytics platform serving 10M requests/day
• Led migration from MySQL to PostgreSQL, cutting query time by 60%
• Designed and shipped Python/FastAPI service for ML inference

Core strengths: Python, FastAPI, PostgreSQL, AWS, Docker, Kubernetes.

Open to connecting with peers, hiring managers, and collaborators. Feel
free to reach out via email or LinkedIn DM.

Experience
Senior Engineer | Acme Corp
2020 - Present
- Built a real-time analytics platform serving 10M requests/day, processing
  50TB of data with sub-second query latency.
- Led migration from MySQL to PostgreSQL, reducing query time by 60%.
- Designed and shipped a Python/FastAPI service for ML inference, handling
  500 req/s with 99.9% uptime.

Engineer | Beta Inc
2017 - 2020
- Designed REST APIs for mobile clients serving 500K MAU.
- Built CI/CD pipelines that reduced deployment time from 30 min to 4 min.

Skills
Python, FastAPI, PostgreSQL, AWS, Docker, Kubernetes, Terraform, Redis,
REST API, GraphQL, Git, CI/CD
"""


def test_parse_linkedin_profile():
    profile = parse_linkedin_profile(SAMPLE_PROFILE)
    assert profile.headline, "Headline should be extracted"
    assert "Senior Backend Engineer" in profile.headline
    assert "Python" in profile.about or "Python" in profile.skills
    assert len(profile.experience) >= 2, f"Expected 2+ experience roles, got {len(profile.experience)}"
    assert "Python" in profile.skills
    print(f"✓ test_parse_linkedin_profile passed (headline={profile.headline[:40]}..., exp={len(profile.experience)}, skills={len(profile.skills)})")


def test_score_profile():
    profile = parse_linkedin_profile(SAMPLE_PROFILE)
    score = score_profile(profile, "Senior Backend Engineer")
    assert 0 <= score.overall <= 100
    assert 0 <= score.headline <= 100
    assert 0 <= score.about <= 100
    # The sample is well-written — overall should be decent
    assert score.overall > 50, f"Well-written profile should score > 50, got {score.overall}"
    print(f"✓ test_score_profile passed (overall={score.overall}, headline={score.headline}, about={score.about}, exp={score.experience}, skills={score.skills})")


def test_optimize_profile_returns_rewrites():
    report = optimize_profile(SAMPLE_PROFILE, "Senior Backend Engineer")
    assert report.score.overall > 0
    # At least 1 headline rewrite should be generated
    assert len(report.headline_rewrites) >= 1, f"Expected ≥1 headline rewrite, got {len(report.headline_rewrites)}"
    # About rewrite should be non-empty
    assert report.about_rewrite, "About rewrite should be generated"
    print(f"✓ test_optimize_profile_returns_rewrites passed (rewrites={len(report.headline_rewrites)})")


def test_optimize_empty_profile_low_score():
    """An empty/minimal profile should score very low."""
    report = optimize_profile("", "Senior Backend Engineer")
    assert report.score.overall < 30, f"Empty profile should score < 30, got {report.score.overall}"
    # Should have critical/high-severity suggestions
    high_severity = [s for s in report.suggestions if s.severity.value in ("critical", "high")]
    assert len(high_severity) > 0
    print(f"✓ test_optimize_empty_profile_low_score passed (score={report.score.overall}, suggestions={len(report.suggestions)})")


def test_weak_headline_detected():
    """A weak/generic headline should trigger a HEADLINE suggestion."""
    weak = """
Looking for opportunities

About
I am a software engineer.

Experience
Engineer | Co
2020 - 2024
Worked on stuff.
"""
    report = optimize_profile(weak, "Senior Backend Engineer")
    headline_suggestions = [s for s in report.suggestions if s.type.value == "headline"]
    assert len(headline_suggestions) > 0, f"Weak headline should trigger suggestion, got types={[s.type.value for s in report.suggestions]}"
    print(f"✓ test_weak_headline_detected passed")


def test_action_verbs_library():
    """Action verbs library should be non-empty and contain common strong verbs."""
    assert "Built" in ACTION_VERBS
    assert "Led" in ACTION_VERBS
    assert "Designed" in ACTION_VERBS
    print(f"✓ test_action_verbs_library passed ({len(ACTION_VERBS)} verbs)")


if __name__ == "__main__":
    test_parse_linkedin_profile()
    test_score_profile()
    test_optimize_profile_returns_rewrites()
    test_optimize_empty_profile_low_score()
    test_weak_headline_detected()
    test_action_verbs_library()
    print(f"\n✓ All 6 LinkedIn optimizer tests passed.")
