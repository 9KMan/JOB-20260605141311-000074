# Plan: Flutter Mobile App

## Phase: 05-flutter-mobile

## Context
Module "Mobile apps" of the 11 in the spec — cross-platform mobile client
(iOS + Android from a single Flutter codebase). The mobile app is the
on-the-go companion to the web app: view ATS scores, browse saved jobs, get
notifications about new job matches, snap-and-upload a resume for instant
ATS scoring.

Tech: Flutter 3.x, Dart 3, Provider for state management, http for API calls,
shared_preferences for token storage, mobile_scanner for QR codes (for the
"scan a job posting QR code" flow). API base URL configurable via
`--dart-define=API_BASE=https://api.example.com`.

## Deliverables (focused — 6 files max)
- `mobile/pubspec.yaml` — Flutter package manifest
- `mobile/lib/main.dart` — App entry, MaterialApp, theme, routes
- `mobile/lib/api/client.dart` — API client (auth + endpoints)
- `mobile/lib/screens/dashboard.dart` — Dashboard screen (job matches, scores)
- `mobile/lib/screens/resume_score.dart` — Resume upload + ATS score display
- `mobile/lib/widgets/score_card.dart` — Reusable score display widget

## Execution
1. Write `pubspec.yaml` with deps (provider, http, shared_preferences, mobile_scanner, flutter_markdown)
2. Build `api/client.dart` — POST /auth/login, GET /resumes, POST /resumes/{id}/score
3. Build `main.dart` with auth gate (login → dashboard)
4. Build dashboard screen showing saved jobs + ATS scores (mock data fallback if API not reachable)
5. Build resume score screen with file picker + score visualization
6. Build score card widget
7. Commit + push

## Mock mode (important)
The PoC must be runnable WITHOUT the FastAPI backend live. Use a `MOCK_API=true`
flag to return canned data so reviewers can `flutter run` and see the UI flow
without needing a database, auth, etc.

## Visual design
- Material 3, light/dark theme support
- Score: circular progress (0-100) + letter grade badge
- Color: green ≥80, yellow 60-79, red <60
- Empty state: "Upload a resume to get started"
