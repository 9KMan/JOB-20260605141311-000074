# Plan: LinkedIn Profile Optimizer

## Phase: 04-linkedin-optimization

## Context
Module 6 of the 11 in the spec: "LinkedIn Optimization" — analyze a user's
LinkedIn profile against a target role and produce a scored report with
concrete rewrites for headline, about, experience bullets, and skills section.
This is the same deterministic-scoring pattern as the ATS engine, applied to
the public-facing LinkedIn profile (not just the resume).

Tech: Python 3.12, FastAPI router, reuses `backend/ats/` patterns. LinkedIn
itself has no official public API for profile data — we'll use a "user pastes
their profile text" input model (copy-paste from LinkedIn's "More" button) so
we don't have to deal with LinkedIn auth, ToS, or rate limits.

## Deliverables (focused — 5 files max)
- `backend/linkedin/optimizer.py` — score + rewrite generator (headline, about, bullets)
- `backend/linkedin/models.py` — Pydantic models (LinkedInProfile, OptimizationReport)
- `backend/linkedin/api.py` — FastAPI router (/linkedin/optimize)
- `backend/tests/test_linkedin_optimizer.py` — 4 unit tests (parse, score, suggest, end-to-end)
- `backend/linkedin/__init__.py` — package init

## Execution
1. Build `LinkedInProfile` parser (paste-text → structured: headline, about, experience, skills)
2. Build scorer: completeness + keyword density + impact language
3. Build rewriter: produce 3 candidate headlines, 3 about-section drafts, rewritten bullets
4. Wire FastAPI router
5. Write 4 tests
6. Commit + push

## Scoring approach
- 30% headline quality (length 40-120 chars, has target role, has value prop)
- 25% about-section quality (length, keyword density, has CTA, first-person)
- 25% experience bullets (action verbs, quantified impact, varied length)
- 10% skills section (≥5 skills, matches target role)
- 10% completeness (location, education, photo URL placeholder, etc.)

## Rewrite rules (deterministic templates)
- Headline: "{target_role} | {value_prop_1} | {value_prop_2}"
- About: opener + 3 experience highlights + 2 skills + CTA
- Bullets: prefix with strong action verb, add quantified placeholder if missing
