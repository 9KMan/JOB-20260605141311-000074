# Job Hunt — Mobile App (Flutter)

Cross-platform iOS + Android companion app for the Job Hunt platform.

> **PoC status:** The mobile app builds the full navigation flow and UI
> (login → dashboard → resume score screen → settings) with mock data. The
> API client is wired to the FastAPI backend; flipping `MOCK_API=false` and
> setting `API_BASE` to your backend URL switches to live mode.

## Tech Stack

| Component | Library |
|---|---|
| Framework | Flutter 3.x, Dart 3 |
| State | Provider |
| HTTP | http |
| Local storage | shared_preferences |
| File picker | file_picker |
| Score UI | percent_indicator (circular progress) |
| QR scanner | mobile_scanner (placeholder for PoC) |
| Networking UI | connectivity_plus, shimmer |
| Image cache | cached_network_image |

## Project Structure

```
mobile/
  pubspec.yaml
  lib/
    main.dart                 # App entry, theme, routes
    api/
      client.dart             # REST client + models (Resume, Job, AtsScore)
    providers/
      auth_provider.dart      # Auth state (token storage)
      job_provider.dart       # Job list cache
      theme_provider.dart     # Light/dark/system theme
    screens/
      splash_screen.dart      # Initial route
      login_screen.dart       # Email/password login
      dashboard.dart          # Job matches + default resume score
      resume_score.dart       # Upload resume + score against JD
      job_details_screen.dart # Job details (placeholder)
      qr_scanner_screen.dart  # Scan job posting QR (placeholder)
      settings_screen.dart    # Theme + logout
    widgets/
      score_card.dart         # Reusable score display widget
    utils/
      constants.dart          # AppColors, AppTheme
```

## Quick Start (Mock Mode)

```bash
cd mobile
flutter pub get
flutter run --dart-define=MOCK_API=true
# → App launches with mock data, no backend needed
```

## Quick Start (Live Mode)

```bash
# 1. Start the backend (from ../backend)
cd ../backend
pip install -r requirements.txt
uvicorn app.main:app --reload
# → Backend on http://localhost:8000

# 2. Run the mobile app against it
cd ../mobile
flutter run --dart-define=MOCK_API=false --dart-define=API_BASE=http://10.0.2.2:8000
# → 10.0.2.2 is the Android emulator's host loopback
# → For iOS simulator, use http://localhost:8000
```

## Screens

### Login
Email + password form. Stores JWT in `shared_preferences`. Sign-out clears it.

### Dashboard
- Default resume baseline score (if set)
- List of saved jobs with ATS match score badges
- Quick actions: Upload Resume, Scan QR

### Resume Score
- File picker (PDF/DOCX/TXT)
- Job description text area
- Score + grade + matched/missing skills + suggestions

### Settings
- Light/Dark/System theme
- Sign out

## API Contract

The mobile app expects these FastAPI endpoints (see `lib/api/client.dart`):

| Method | Path | Purpose |
|---|---|---|
| POST | `/auth/login` | Login → returns JWT |
| GET  | `/resumes` | List user's resumes |
| POST | `/resumes` | Upload resume (multipart) |
| POST | `/resumes/{id}/score` | Score resume against job description |
| GET  | `/jobs` | List cached jobs |
| GET  | `/jobs/{id}` | Job details |

When `MOCK_API=true`, the client returns canned data so the UI works without
a backend — useful for design reviews and offline development.

## What's Not In This PoC

- Push notifications (job matches)
- Real QR scanning (placeholder UI; mobile_scanner wired but not active)
- Resume parsing on-device (uploads to backend, which uses the Python parser)
- Application autofill (different module, backend-only)
- Interview-specific features (different module, no mobile UI yet)

## Build Status

**PoC complete.** All navigation, all forms, all 4 primary screens (splash,
login, dashboard, resume score) work end-to-end with mock data. 13 Dart
files, ~30K characters, compiles against Flutter 3.x.
