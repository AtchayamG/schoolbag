# Schoolbag Test Status & Verification Report

- Date: September 2026
- Branch: `worker/agy/SB-002`
- Total Spend: **₹0.00 / \$0.00**

---

## 1. Backend Pytest Suite (`services/school_service/tests/`)

- Total Tests: **22**
- Passed: **22**
- Failed: **0**
- Execution Time: **13.49s**

| Test File | Tests | Status | Scope |
| :--- | :--- | :--- | :--- |
| `test_workflow_slice.py` | 1 | **PASSED** | Complete 9-step vertical slice: workspace session, intake, 2+ action extraction, deduplication, deadline normalizer, reminder draft, 403 assistant rejection, parent approval & completion persistence, 422 & 503 failures |
| `test_config_and_security.py` | 4 | **PASSED** | Production environment detector, nosniff/DENY security headers, production origin enforcement (403 ORIGIN_REFUSED), preset catalog integrity |
| `test_workspace_isolation.py` | 3 | **PASSED** | Session cookie issuance, cross-workspace 404 isolation, 50-notice workspace capacity enforcement |
| `test_deduplication.py` | 4 | **PASSED** | Whitespace/case normalization resilience, Idempotency-Key replay, 409 conflict on altered payload, header vs body mismatch |
| `test_human_approval.py` | 2 | **PASSED** | Assistant 403 rejection on fees and consent, parent approval, optimistic concurrency locking 409 conflict |
| `test_deadline_normalizer.py` | 3 | **PASSED** | ISO timestamp preservation, YYYY-MM-DD date normalization, relative weekday and urgent parsing in IST (+05:30) |
| `test_fullstack_packaging.py` | 3 | **PASSED** | `/api/health` and `/api/ready` disclosures, strict JSON 404 for unknown `/api/*`, static SPA serving and fallback |
| `test_transactional_concurrency.py` | 2 | **PASSED** | Full workflow slice on real ephemeral PostgreSQL 16.10, two-connection concurrent optimistic conflict |

---

## 2. Frontend Vitest Suite (`apps/web/src/test/`)

- Total Tests: **6**
- Passed: **6**
- Failed: **0**
- Execution Time: **2.46s**

| Test Case | Status | Verified Functionality |
| :--- | :--- | :--- |
| `renders evaluator guide, zero spend declaration, and minimal identifier guarantee` | **PASSED** | Header badges, task ID, zero spend disclosure, capacity badge, child filters |
| `renders action card with normalized deadline and human gate demonstration button` | **PASSED** | Action card layout, amount chip, IST deadline, approval buttons |
| `handles simulated assistant approval rejection with HTTP 403 error banner` | **PASSED** | Assistant approval triggers 403 and displays prominent red rejection banner |
| `renders notice card with synthetic metadata and child context` | **PASSED** | Notice card source type, child alias chip, class chip |
| `renders audit event stream with security rejection event` | **PASSED** | Immutable event stream displaying `approval_rejected_human_gate` and notes |
| `renders provenance card with truthful disclosures` | **PASSED** | Truthful engine disclosure, Kovai Vidya Mandir provenance, ₹0.00 spend |

---

## 3. 19-Stage Release Smoke Suite (`scripts/release_smoke.py`)

- Total Stages: **19**
- Passed: **19**
- Failed: **0**

```
===========================================================================
  ALL 19/19 STAGES PASSED SUCCESSFULLY!
===========================================================================
```

---

## 4. Static Analysis & Linting

- **Ruff Linter**: `All checks passed!` (0 errors)
- **Ruff Formatter**: `27 files already formatted` (0 reformats needed)
- **Mypy Type Checker**: `Success: no issues found in 27 source files` (0 errors)
- **ESLint**: `0 warnings, 0 errors`
- **TypeScript Compiler (`tsc`)**: `0 errors`
