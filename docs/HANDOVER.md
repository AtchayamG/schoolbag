# Schoolbag Handover & Evaluator Quickstart Guide

## Project Summary
- **Task ID**: `SB-005` (Final Production Packaging & Submission)
- **Product**: Schoolbag (Project 3)
- **Track**: Everyday Agents (Agents for Humans Hackathon)
- **Worktree / Directory**: `03_SCHOOLBAG/`
- **Active Branch**: `worker/agy/SB-005`
- **Total Spend**: **₹0.00 / $0.00** (Zero external paid APIs, deterministic synthetic engine + Groq free tier / offline mock transport)
- **Zero Secrets**: No API keys or credentials stored in repository

---

## 1. Quick Verification Commands

### Run Full 22-Stage Release Smoke Suite
```bash
cd services/school_service
.\.venv\Scripts\python.exe ..\..\scripts\release_smoke.py
```
*Expected Output*: `ALL 22/22 STAGES PASSED SUCCESSFULLY!`

### Run 11-Stage Live Canary Suite
```bash
cd 03_SCHOOLBAG
.\services\school_service\.venv\Scripts\python.exe scripts\live_canary.py
```
*Expected Output*: `ALL 11 CANARY STAGES PASSED SUCCESSFULLY!`

### Run Backend Pytest Suite (37 Tests)
```bash
cd services/school_service
.\.venv\Scripts\python.exe -m pytest -v
```
*Expected Output*: `37 passed in ~16.5s` (including 3 RFC 5545 calendar tests, 12 Strands agent tests, ephemeral PostgreSQL 16, and production security tests).

### Run Frontend Vitest Suite (10 Tests)
```bash
cd apps/web
cmd.exe /c npm test -- --run
```
*Expected Output*: `10 passed (1 file)`.

### Verify Web Build & Linting
```bash
cd apps/web
cmd.exe /c npm run lint
cmd.exe /c npm run build
```
*Expected Output*: ESLint 0 warnings, Vite production build completed to `apps/web/dist/`.

### Run Python Quality Checks
```bash
cd 03_SCHOOLBAG
.\services\school_service\.venv\Scripts\ruff.exe check services/school_service/src services/school_service/tests scripts
.\services\school_service\.venv\Scripts\ruff.exe format --check services/school_service/src services/school_service/tests scripts
```
*Expected Output*: All passed with 0 errors across all 37 source files.

---

## 2. Interactive Browser Review

To launch the fullstack application in browser review mode:
```bash
cd 03_SCHOOLBAG
.\services\school_service\.venv\Scripts\python.exe scripts\browser_review_server.py --port 8000
```
Then navigate to `http://localhost:8000` to review:
1. **Notice Feed**: Ingest synthetic school WhatsApp forwards for Kovai Vidya Mandir, Coimbatore.
2. **Strands AI Advisory**: Click **"Analyze with Strands AI"** on any notice to trigger the bounded tool advisory loop.
3. **Mandatory Human Gate**: Try clicking "Simulate Assistant Approval (Expect 403)" to verify non-parent approval blocking.
4. **Parent Approval**: Click "Parent Sign & Authorize" to simulate human parent authorization.
5. **iCalendar (.ics) Export**: Click "Export .ics" on any action to download an RFC 5545 calendar event with a 2-hour pre-deadline alarm reminder.
6. **WhatsApp Family Draft**: Click "WhatsApp Draft" to copy an instant formatted family reminder to your clipboard.
7. **Family Weekly Board**: Click "Family Weekly Board (Visual Diary)" tab to view the multi-child side-by-side view (Kavya & Arun), aggregate pending fee totals, family deadline overlap detection, and consolidated `.ics` family calendar feed.
8. **Truthful Disclosures**: Inspect the footer provenance card disclosing the rule engine, Strands agent seam, and zero-spend declarations.

---

## 3. Submission Documentation
- **Demo Video Script**: `docs/DEMO_VIDEO_SCRIPT.md` (180-second timed production script with captions and cues).
- **Devpost Submission**: `docs/DEVPOST_SUBMISSION.md` (Everyday Agents track submission copy).
- **Milestone Acceptance Records**: `docs/SB-001_ACCEPTANCE.md` through `docs/SB-005_ACCEPTANCE.md`.
