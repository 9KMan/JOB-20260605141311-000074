# AI Platform for Jobseekers — Production PoC

A working proof-of-concept for the full-stack AI jobseeker platform: ATS resume
scoring engine, async FastAPI backend, and a Manifest V3 browser extension.
Three client surfaces (web, mobile, extension) are scaffolded — the core
intellectual property is in the deterministic, explainable ATS scoring engine.

> **Why this PoC matters:** most "AI resume" tools wrap an LLM chat completion.
> This platform uses **TF-IDF cosine similarity + weighted skill matching** —
> the score is reproducible, auditable, and explainable. No GPU, no LLM API
> cost, no hallucination on scores.

---

## 🎯 Business Problem Solved

**Who suffers:** Jobseekers applying to dozens of roles weekly waste hours
tailoring resumes that still get rejected by ATS filters they can't see.
**What breaks:** Their resume keywords don't match the job description, but
they have no way to know the gap before submitting. Recruiters reject
>75% of resumes before a human sees them.
**What this delivers:** A real-time ATS score (0-100) with per-section
breakdown and concrete improvement suggestions (missing skills, weak verbs,
length issues) — shown inline in the browser as you read any job posting.

---

## Tech Stack

| Layer | Tech |
|---|---|
| ATS Engine | Python 3.12, pdfplumber, python-docx, scikit-learn (TF-IDF) |
| Backend | FastAPI (async), SQLAlchemy 2.0, Alembic, PostgreSQL |
| Auth | JWT (python-jose), bcrypt password hashing |
| Extension | Chrome Manifest V3, vanilla JS, REST |
| Mobile (scaffolded) | Flutter (see [docs/mobile-scope.md](docs/)) |

---

## Quick Start (Backend)

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env       # set DATABASE_URL + JWT_SECRET
alembic upgrade head        # apply migrations
uvicorn app.main:app --reload
# → http://localhost:8000/docs (Swagger UI)
```

## Quick Start (Extension)

```bash
# Chrome/Edge:
# 1. Visit chrome://extensions
# 2. Enable "Developer mode"
# 3. Click "Load unpacked" → select the extension/ directory

# See extension/README.md for the full dev workflow.
```

## Quick Start (ATS Engine only)

```bash
cd backend
python -c "
from ats.parser import parse_resume
from ats.scorer import score_against_job
resume = parse_resume('../examples/sample_resume.txt')
job    = open('../examples/sample_job.txt').read()
result = score_against_job(resume, job)
print(f'Match: {result.score}/100')
print('Missing skills:', result.missing_skills)
"
```

---

## API Overview

| Method | Path | Description |
|---|---|---|
| POST | `/auth/register` | Create account (email + password) |
| POST | `/auth/login` | Returns JWT (30-day) |
| GET  | `/auth/me` | Current user profile |
| POST | `/resumes` | Upload resume (PDF/DOCX) |
| GET  | `/resumes/{id}` | Get parsed resume |
| POST | `/resumes/{id}/score` | Score resume against a job description |
| GET  | `/jobs` | List cached job postings |
| GET  | `/jobs/{id}` | Get job details |
| POST | `/applications` | Track a job application |

Full OpenAPI spec: `http://localhost:8000/docs`

---

## Project Structure

```
backend/
  ats/                    # ★ The IP — deterministic scoring engine
    parser.py             #   Resume → structured sections
    scorer.py             #   TF-IDF + weighted skill matching
    suggestions.py        #   Improvement advice
    models.py             #   Pydantic data models
  app/
    main.py               #   FastAPI app entry
    config.py             #   Settings (env-driven)
    database.py           #   Async SQLAlchemy
    models/               #   User, Resume, Job, Application
    api/                  #   /auth, /resumes, /jobs, /applications
    security.py           #   JWT + bcrypt
    dependencies.py       #   Auth dependency injection
  migrations/             #   Alembic schema migrations
  tests/                  #   pytest + httpx async tests
  requirements.txt
  .env.example

extension/
  manifest.json           # Manifest V3
  popup/                  # Side panel UI
  background/             # Service worker
  content/                # DOM scraper for job portals
  lib/api.js              # Backend client

docs/                     # Architecture + extension guides
examples/                 # Sample resume + job for testing
```

---

## What This PoC Demonstrates

✅ **Real, working ATS scoring** — not a mock, not an LLM wrapper. The scorer is
deterministic and auditable (same input → same score, every time).
✅ **Production-grade async backend** — SQLAlchemy 2.0 + Alembic + JWT + bcrypt
matches what a real platform would ship.
✅ **Browser extension with real DOM scraping** — works on Upwork, LinkedIn,
Indeed (skeleton ready for the cross-platform story).
✅ **Clear extension path** — every layer is structured to add the remaining
9 modules (payment gateway, mock interview, live interview, LinkedIn optimizer,
etc.) without rewrites.

## What's Not In This PoC (scaffolded for v2)

| Module | Status | Notes |
|---|---|---|
| AI cover letter | scaffolded | Reuses backend/resume + LLM hook |
| Application autofill | scaffolded | Extension skeleton has the data model |
| Multi-portal search | scaffolded | `/jobs` endpoint + scraper ready |
| LinkedIn optimization | not started | Out of PoC scope |
| AI mock interview | not started | Out of PoC scope |
| Payment gateway | not started | Out of PoC scope |
| Live interview assistant | not started | Out of PoC scope |
| Mobile (Flutter) | not started | Cross-platform story |
| Dashboards | not started | Out of PoC scope |

## Why The Remaining 9 Modules Are Out of Scope for $2k Fixed-Price

A 5-figure scope (web + extension + mobile × 11 modules × AI/ML + payments +
ATS scoring) is realistically a $40-80k engagement at market rates. This PoC
shows **the hardest 2 modules** (deterministic ATS engine + production backend
architecture) — proof that the rest of the platform is buildable on the same
foundation, not a fantasy deliverable.

## License

MIT — see LICENSE.

---

**Built by:** KMan (Mongkolpoj Phanutaecha) | AI-Augmented Engineering Factory
