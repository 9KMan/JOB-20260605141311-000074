# AI Platform for Jobseekers — Production PoC

A working proof-of-concept for the full-stack AI jobseeker platform: ATS
resume scoring engine, LinkedIn profile optimizer, async FastAPI backend,
Manifest V3 browser extension, and a Flutter mobile app. The two highest-IP
modules (ATS scoring + LinkedIn optimization) are fully implemented; the
backend, extension, and mobile app demonstrate the full architecture.

> **Why this PoC matters:** most "AI resume" tools wrap an LLM chat
> completion. This platform uses **TF-IDF cosine similarity + weighted
> skill matching** for both resume ATS scoring AND LinkedIn profile
> optimization. The scores are reproducible, auditable, and explainable.
> No GPU, no LLM API cost, no hallucination on scores.

---

## 🎯 Business Problem Solved

**Who suffers:** Jobseekers applying to dozens of roles weekly waste hours
tailoring resumes that still get rejected by ATS filters they can't see.
**What breaks:** Their resume keywords don't match the job description, but
they have no way to know the gap before submitting. Recruiters reject
>75% of resumes before a human sees them.
**What this delivers:** Real-time ATS scoring (0-100) AND LinkedIn profile
optimization with concrete improvement suggestions (missing skills, weak
verbs, length issues) — shown inline in the browser as you read any job
posting, and on mobile as you snap a resume.

---

## Modules Implemented (5 of 11)

| # | Module | Status | Location |
|---|---|---|---|
| 1 | AI Resume Creation | scaffolded | (parser extracts sections, used by scorer) |
| 2 | AI Cover Letter | not started | (LLM hook scaffolded in backend) |
| 3 | **ATS Scans + Resume Score + Job Match** | **✅ WORKING** | `backend/ats/` |
| 4 | Application Autofill | scaffolded | (extension skeleton has data model) |
| 5 | Multi-Portal Job Search | scaffolded | (`/jobs` endpoint ready) |
| 6 | **LinkedIn Optimization** | **✅ WORKING** | `backend/linkedin/` |
| 7 | AI Mock Interview | not started | (out of PoC scope) |
| 8 | Payment Gateway | not started | (out of PoC scope) |
| 9 | Interview-Specific Prep | not started | (out of PoC scope) |
| 10 | Live AI Interview Assistant | not started | (out of PoC scope) |
| 11 | Dashboards | scaffolded | (mobile app dashboard works) |

**2 fully-implemented modules** (ATS Engine + LinkedIn Optimizer) with
deterministic scoring, working tests, and reusable rewrite logic.

---

## Tech Stack

| Layer | Tech |
|---|---|
| ATS Engine | Python 3.12, pdfplumber, python-docx, scikit-learn (TF-IDF) |
| LinkedIn Optimizer | Python 3.12, FastAPI, deterministic rewrite templates |
| Backend | FastAPI (async), SQLAlchemy 2.0, Alembic, PostgreSQL |
| Auth | JWT (python-jose), bcrypt password hashing |
| Extension | Chrome Manifest V3, vanilla JS, REST |
| Mobile | Flutter 3.x, Dart 3, Provider, percent_indicator, file_picker |

---

## Quick Start (Backend)

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-ats.txt
cp .env.example .env       # set DATABASE_URL + JWT_SECRET
alembic upgrade head        # apply migrations
uvicorn app.main:app --reload
# → http://localhost:8000/docs (Swagger UI)
```

## Quick Start (Mobile — Mock Mode)

```bash
cd mobile
flutter pub get
flutter run --dart-define=MOCK_API=true
# → App launches with mock data, no backend needed
```

## Quick Start (Extension)

```bash
# Chrome/Edge:
# 1. Visit chrome://extensions
# 2. Enable "Developer mode"
# 3. Click "Load unpacked" → select the extension/ directory
```

## Quick Start (ATS Engine only)

```bash
cd backend
PYTHONPATH=. python3 tests/test_ats_scorer.py
# → All 8 tests pass
PYTHONPATH=. python3 tests/test_linkedin_optimizer.py
# → All 6 tests pass
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
| POST | `/linkedin/optimize` | Score + rewrite a LinkedIn profile |
| GET  | `/jobs` | List cached job postings |
| GET  | `/jobs/{id}` | Get job details |
| POST | `/applications` | Track a job application |

Full OpenAPI spec: `http://localhost:8000/docs`

---

## Project Structure

```
backend/
  ats/                        # ✅ Module 3 — ATS Resume Scoring Engine
    parser.py                 #   Resume → structured sections
    scorer.py                 #   TF-IDF + weighted skill matching
    models.py                 #   Pydantic v2 schemas
    __init__.py               #   Public API
  linkedin/                   # ✅ Module 6 — LinkedIn Profile Optimizer
    optimizer.py              #   Score + 3 headline rewrites + about template
    models.py                 #   Pydantic v2 schemas
    api.py                    #   /linkedin/optimize router
    __init__.py               #   Public API
  app/
    main.py                   #   FastAPI app entry
    config.py                 #   Settings (env-driven)
    database.py               #   Async SQLAlchemy
    models/                   #   User, Resume, Job, Application
    api/                      #   /auth, /resumes, /jobs, /applications
    security.py               #   JWT + bcrypt
    dependencies.py           #   Auth dependency injection
  migrations/                 #   Alembic schema migrations
  tests/                      #   14 passing tests (8 ATS + 6 LinkedIn)
  requirements.txt
  requirements-ats.txt

extension/
  manifest.json               # Manifest V3
  popup/                      # Side panel UI
  background/                 # Service worker
  content/                    # DOM scraper for job portals
  lib/api.js                  # Backend client

mobile/
  pubspec.yaml                # Flutter 3.x manifest
  lib/
    main.dart                 # App entry, theme, named routes
    api/client.dart           # REST client + models
    providers/                # auth, job, theme
    screens/                  # splash, login, dashboard, resume_score, ...
    widgets/score_card.dart   # Reusable score display
    utils/constants.dart      # AppColors, AppTheme
  README.md                   # Mobile-specific setup

docs/                         # Architecture + extension guides
examples/                     # Sample resume + job for testing
```

---

## What This PoC Demonstrates

✅ **Real, working ATS scoring** — not a mock, not an LLM wrapper. The
scorer is deterministic and auditable (same input → same score, every time).
8/8 unit tests pass.
✅ **Real, working LinkedIn optimizer** — same deterministic philosophy.
5-section scoring (headline, about, experience, skills, completeness) plus
3 candidate headlines, 3-paragraph about-section template, and bullet
rewriter. 6/6 unit tests pass.
✅ **Production-grade async backend** — SQLAlchemy 2.0 + Alembic + JWT +
bcrypt matches what a real platform would ship.
✅ **Browser extension with real DOM scraping** — works on Upwork,
LinkedIn, Indeed (skeleton ready for cross-platform story).
✅ **Cross-platform mobile app** — Flutter 3.x, full navigation, working
upload flow with file_picker, working score display with percent_indicator.
Runs in mock mode without backend.
✅ **14 unit tests, all passing** — deterministic scoring is testable
in a way LLM-based scoring never will be.

## What's Not In This PoC (scaffolded or out of scope for $2k fixed-price)

| Module | Status | Notes |
|---|---|---|
| AI cover letter | scaffolded | Reuses backend/resume + LLM hook |
| Application autofill | scaffolded | Extension skeleton has the data model |
| Multi-portal search | scaffolded | `/jobs` endpoint + scraper ready |
| AI mock interview | not started | Out of PoC scope |
| Payment gateway | not started | Out of PoC scope |
| Live interview assistant | not started | Out of PoC scope |
| Push notifications | not started | Out of PoC scope |
| Real QR scanning | placeholder | mobile_scanner wired but not active |

## Why The Remaining Modules Are Out of Scope for $2k Fixed-Price

A 5-figure scope (web + extension + mobile × 11 modules × AI/ML + payments +
ATS scoring + LinkedIn optimization) is realistically a $40-80k engagement
at market rates. This PoC shows **the 2 highest-IP modules** (deterministic
ATS engine + LinkedIn optimizer) plus a working full-stack scaffold
(backend, extension, mobile) — proof that the rest of the platform is
buildable on the same foundation, not a fantasy deliverable.

## License

MIT — see LICENSE.

---

**Built by:** KMan (Mongkolpoj Phanutaecha) | AI-Augmented Engineering Factory

