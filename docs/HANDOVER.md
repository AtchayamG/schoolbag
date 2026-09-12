# Schoolbag Handover & Evaluator Quickstart Guide

## Project Summary
- **Task ID**: `SB-002` (Base: `SB-001`)
- **Product**: Schoolbag (Project 3)
- **Worktree / Directory**: `03_SCHOOLBAG/`
- **Active Branch**: `worker/agy/SB-002`
- **Total Spend**: **₹0.00 / \$0.00** (Zero external paid APIs, deterministic synthetic engine)
- **Zero Secrets**: No API keys or credentials stored or required

---

## 1. Quick Verification Commands

### Run Full 19-Stage Release Smoke Suite
```bash
cd services/school_service
.\.venv\Scripts\python.exe ..\..\scripts\release_smoke.py
```
*Expected Output*: `ALL 19/19 STAGES PASSED SUCCESSFULLY!`

### Run Backend Pytest Suite (22 Tests)
```bash
cd services/school_service
.\.venv\Scripts\python.exe -m pytest -v
```
*Expected Output*: `22 passed in ~13.5s` (including ephemeral PostgreSQL 16 and production security tests).

### Run Frontend Vitest Suite (6 Tests)
```bash
cd apps/web
npm test -- --reporter=dot
```
*Expected Output*: `6 passed (1 file)`.

### Verify Web Build & Linting
```bash
cd apps/web
npm run lint
npm run build
```
*Expected Output*: ESLint 0 warnings, Vite production build completed to `apps/web/dist/`.

### Run Python Quality Checks
```bash
cd services/school_service
.\.venv\Scripts\ruff.exe check src tests
.\.venv\Scripts\ruff.exe format --check src tests
.\.venv\Scripts\mypy.exe src tests
```
*Expected Output*: All passed with 0 errors across 27 source files.

---

## 2. Interactive Browser Review

To launch the fullstack application in browser review mode:
```bash
cd 03_SCHOOLBAG
.\services\school_service\.venv\Scripts\python.exe scripts\browser_review_server.py --port 8000
```
Open **http://127.0.0.1:8000** in your browser:
1. Review the **Evaluator Guide Banner** at the top verifying task ID `SB-002`, version `v0.2.0`, zero spend, minimal child identifiers, and human authority gate rules.
2. Toggle the **"60-Second Evaluator Tour"** accordion to view the 4-step quickstart walkthrough.
3. Click **"Ingest School Notice"** and select one of the 1-click synthetic presets for *Kovai Vidya Mandir, Coimbatore*:
   - Preset 1: Science Exhibition Kit Fee (Class 5-B Kavya, ₹150)
   - Preset 2: Annual Day Field Trip & Costume Fee (Class 5-B Kavya, ₹350, Ooty consent)
   - Preset 3: Mid-Term Examination Schedule (Class 8-A Arun)
   - Preset 4: Inter-School Athletics Meet (Class 8-A Arun, ₹200 bus transport fee, consent slip)
4. Submit and observe extracted actions with normalized deadlines in IST (`+05:30`).
5. On the Fee Payment or Consent card, click **"Simulate Assistant Approval (Expect 403)"**:
   - The UI displays an explicit rejection banner with `HTTP 403 - HUMAN_APPROVAL_REQUIRED` and the backend refusal message, proving automated agents cannot sign consent or spend money.
6. Click **"Parent Sign & Authorize"**:
   - The action updates to `Parent Authorized` with timestamp.
7. Click **"Mark Completed"**:
   - The action transitions to completed.
8. Check the **Audit Event Log** column on the right:
   - Contains immutable records for ingestion, extraction, 403 rejection, parent authorization, and completion.
