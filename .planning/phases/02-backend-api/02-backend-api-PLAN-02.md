# Plan: FastAPI Backend with Auth + Job/Resume/Application Models

## Phase: 02-backend-api

## Context
After the ATS engine is built, we need a REST API to expose it. This is the
production-ready backend that ties everything together: user auth, resume
upload, ATS scoring endpoint, job description endpoint, application tracking.

Tech: FastAPI (async), SQLAlchemy 2.0 (async), Alembic migrations,
PostgreSQL, JWT auth (python-jose), bcrypt password hashing, pydantic v2
validation. The async stack handles the eventual mobile + browser extension
client load.

## Deliverables
- `backend/app/main.py` — FastAPI app entry point
- `backend/app/config.py` — Settings (env-driven, Pydantic BaseSettings)
- `backend/app/database.py` — Async SQLAlchemy engine + session
- `backend/app/models/user.py` — User SQLAlchemy model
- `backend/app/models/resume.py` — Resume model
- `backend/app/models/job.py` — Job model (cached from job portals)
- `backend/app/models/application.py` — Application model
- `backend/app/api/auth.py` — /register, /login, /me endpoints
- `backend/app/api/resumes.py` — /resumes upload, /resumes/{id}/score endpoints
- `backend/app/api/jobs.py` — /jobs list, /jobs/{id} endpoints
- `backend/app/api/applications.py` — /applications endpoints
- `backend/app/dependencies.py` — JWT auth dependency
- `backend/app/security.py` — Password hashing, token utilities
- `backend/alembic.ini` + `backend/alembic/env.py` — Migration setup
- `backend/migrations/versions/0001_initial.py` — Initial schema
- `backend/requirements.txt` — Pinned dependencies
- `backend/.env.example` — Environment variable template
- `backend/tests/test_auth.py` — Auth flow tests
- `backend/tests/test_resume_api.py` — Resume API tests
- `backend/README.md` — Backend-specific setup

## Execution
1. Build async DB layer with SQLAlchemy 2.0
2. Build JWT auth (register, login, /me)
3. Wire ATS engine from Phase 01 into /resumes/{id}/score
4. Add Alembic migrations
5. Write API tests (httpx AsyncClient + pytest-asyncio)
6. Run tests, fix any failures
7. Commit and push
