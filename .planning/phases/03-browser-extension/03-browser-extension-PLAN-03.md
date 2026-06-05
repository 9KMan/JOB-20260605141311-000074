# Plan: Browser Extension Skeleton (Manifest V3)

## Phase: 03-browser-extension

## Context
A browser extension is one of the three client surfaces (web app, mobile,
extension). For an Upwork PoC, we need to demonstrate cross-platform reach.
This is a focused Chrome/Edge/Firefox-compatible extension (Manifest V3)
that:
- Detects job posting pages on Upwork, LinkedIn, Indeed
- Extracts job title, company, description
- Sends to backend /jobs endpoint for ATS scoring against user's saved resumes
- Shows a side-panel with the match score and "Apply with this resume" button

This is a skeleton, not a full production extension — enough to show the
client surface, the auth flow, and the cross-platform story.

## Deliverables
- `extension/manifest.json` — Manifest V3 config
- `extension/popup/popup.html` — Popup UI
- `extension/popup/popup.css` — Styles
- `extension/popup/popup.js` — Popup logic (calls /jobs/score)
- `extension/background/service-worker.js` — Service worker
- `extension/content/extract-job.js` — DOM scraper for job portals
- `extension/lib/api.js` — Backend API client (auth + endpoints)
- `extension/icons/icon-16.png` — Placeholder icon (or SVG)
- `extension/icons/icon-48.png` — Placeholder icon
- `extension/icons/icon-128.png` — Placeholder icon
- `extension/README.md` — Installation + dev mode instructions
- `docs/extension-architecture.md` — How extension talks to backend

## Execution
1. Build manifest.json with required permissions (storage, activeTab, scripting)
2. Build popup UI showing match score
3. Build content script that extracts job info from Upwork/LinkedIn/Indeed
4. Build service worker that handles cross-tab communication
5. Wire to backend /jobs/score endpoint
6. Document install (chrome://extensions → load unpacked)
7. Commit and push
