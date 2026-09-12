# Schoolbag Handover & Evaluator Quickstart Guide

## Project Summary
- **Task ID**: `SB-001`
- **Product**: Schoolbag (Project 3)
- **Worktree / Directory**: `03_SCHOOLBAG/`
- **Branch**: `worker/agy/SB-001`
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

### Run Backend Pytest Suite
```bash
cd services/school_service
.\.venv\Scripts\python.exe -m pytest -v
```
*Expected Output*: `18 passed in ~14s` (including real ephemeral PostgreSQL 16 tests).

### Run Frontend Vitest Suite
```bash
cd apps/web
npm test -- --reporter=dot
```
*Expected Output*: `6 passed (1 file)`.

### Verify Web Build
```bash
cd apps/web
npm run build
```
*Expected Output*: Vite production build completed to `apps/web/dist/`.

### Run Python Quality Checks
```bash
cd services/school_service
.\.venv\Scripts\ruff.exe check src tests
.\.venv\Scripts\ruff.exe format --check src tests
.\.venv\Scripts\mypy.exe src tests
```
*Expected Output*: All passed with 0 errors.

---

## 2. Interactive Browser Review

To launch the fullstack application in browser review mode:
```bash
cd 03_SCHOOLBAG
.\services\school_service\.venv\Scripts\python.exe scripts\browser_review_server.py --port 8000
```
Open **http://127.0.0.1:8000** in your browser:
1. Review the **Evaluator Guide Banner** at the top verifying task ID `SB-001`, zero spend, minimal child identifiers, and human authority gate rules.
2. Click **"Ingest School Notice"** and select one of the 1-click synthetic presets for *Kovai Vidya Mandir, Coimbatore* (e.g., Annual Day Field Trip & Costume Fee).
3. Submit and observe 3 extracted actions:
   - Fee Payment (₹350 INR)
   - Consent Form (Field Trip to Ooty)
   - Materials to Bring (Chart paper & clay models)
4. Notice the normalized deadline in IST (`+05:30`).
5. On the Fee Payment or Consent card, click **"Simulate Assistant Approval (Expect 403)"**:
   - The UI displays an explicit rejection banner with `HTTP 403 - HUMAN_APPROVAL_REQUIRED` and the backend refusal message, proving automated agents cannot sign consent or spend money.
6. Click **"Parent Sign & Authorize"**:
   - The action updates to `Parent Authorized` with timestamp.
7. Click **"Mark Completed"**:
   - The action transitions to completed.
8. Check the **Audit Event Log** column on the right:
   - Contains immutable records for ingestion, extraction, 403 rejection, parent authorization, and completion.
