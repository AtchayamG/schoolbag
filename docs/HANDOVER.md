# Schoolbag Handover & Evaluator Quickstart Guide

## Project Summary
- **Task ID**: `SB-003` (Base: `SB-002`)
- **Product**: Schoolbag (Project 3)
- **Worktree / Directory**: `03_SCHOOLBAG/`
- **Active Branch**: `worker/agy/SB-003`
- **Total Spend**: **₹0.00 / \$0.00** (Zero external paid APIs, deterministic synthetic engine + Groq free tier / offline mock transport)
- **Zero Secrets**: No API keys or credentials stored in repository

---

## 1. Quick Verification Commands

### Run Full 20-Stage Release Smoke Suite
```bash
cd services/school_service
.\.venv\Scripts\python.exe ..\..\scripts\release_smoke.py
```
*Expected Output*: `ALL 20/20 STAGES PASSED SUCCESSFULLY!`

### Run Backend Pytest Suite (34 Tests)
```bash
cd services/school_service
.\.venv\Scripts\python.exe -m pytest -v
```
*Expected Output*: `34 passed in ~15.4s` (including 12 Strands agent tests, ephemeral PostgreSQL 16, and production security tests).

### Run Frontend Vitest Suite (8 Tests)
```bash
cd apps/web
cmd.exe /c npm test -- --run
```
*Expected Output*: `8 passed (1 file)`.

### Verify Web Build & Linting
```bash
cd apps/web
cmd.exe /c npm run lint
cmd.exe /c npm run build
```
*Expected Output*: ESLint 0 warnings, Vite production build completed to `apps/web/dist/`.

### Run Python Quality Checks
```bash
cd services/school_service
.\.venv\Scripts\ruff.exe check src tests
.\.venv\Scripts\ruff.exe format --check src tests
.\.venv\Scripts\mypy.exe src
```
*Expected Output*: All passed with 0 errors across all source files.

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
5. **Truthful Disclosures**: Inspect the footer provenance card disclosing the rule engine, Strands agent seam, and zero-spend declarations.
