# Plan: AI Resume Parsing + ATS Score Engine

## Phase: 01-ai-resume-ats

## Context
This is the core intellectual property of the platform. Most "AI resume" tools on
Upwork are wrappers around OpenAI's chat completion. We'll build a deterministic
ATS scoring engine that:
- Parses a resume PDF/DOCX into structured sections
- Extracts skills, years of experience, education, certifications
- Scores a resume against a job description using weighted keyword matching
- Provides concrete improvement suggestions (missing keywords, weak verbs, length)
- Returns explainable score (0-100) with per-section breakdown

Tech: Python 3.12, FastAPI, pdfplumber, python-docx, scikit-learn (TF-IDF),
PostgreSQL (job_id, resume_id, score history). No LLM dependency for scoring —
this makes the score reproducible and auditable, which is a real differentiator.

## Deliverables
- `backend/ats/__init__.py` — package init
- `backend/ats/parser.py` — Resume parser (PDF/DOCX → structured dict)
- `backend/ats/scorer.py` — ATS scoring engine (TF-IDF + keyword weighting)
- `backend/ats/suggestions.py` — Improvement suggestion generator
- `backend/ats/models.py` — Pydantic data models
- `backend/tests/test_ats_scorer.py` — Unit tests for the scorer
- `docs/ats-architecture.md` — Architecture overview
- `examples/sample_resume.txt` — Sample resume for testing

## Execution
1. Read SPEC.md §3 (AI Resume creation) and §4 (ATS Scans)
2. Build parser that handles PDF + DOCX, returns structured sections
3. Build scorer: TF-IDF cosine similarity + weighted skill matching
4. Build suggestions: identify missing required skills, weak action verbs, length issues
5. Write unit tests with sample resume
6. Run tests, fix any failures
7. Commit and push
