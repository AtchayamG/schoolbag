# Schoolbag Test Status & Verification Report

- Date: September 2026
- Branch: `worker/agy/SB-001`
- Total Spend: **₹0.00 / \$0.00**

---

## 1. Backend Pytest Suite (`services/school_service/tests/`)

- Total Tests: **18**
- Passed: **18**
- Failed: **0**
- Execution Time: **14.33s**

| Test File | Tests | Status | Scope |
| :--- | :--- | :--- | :--- |
| `test_workflow_slice.py` | 1 | **PASSED** | Complete 9-step vertical slice: workspace session, intake, 2+ action extraction, deduplication, deadline normalizer, reminder draft, 403 assistant rejection, parent approval & completion persistence, 422 & 503 failures |
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
- Execution Time: **2.78s**

| Test Case | Status | Verified Functionality |
| :--- | :--- | :--- |
| `renders evaluator guide, zero spend declaration, and minimal identifier guarantee` | **PASSED** | Header badges, task ID `SB-001`, zero spend disclosure, capacity badge, child filters |
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
  SCHOOLBAG (SB-001) - 19-STAGE END-TO-END RELEASE SMOKE SUITE
===========================================================================
  [STAGE 01/19] PASS: Workspace Session Cookie Issuance - ws_id=ws_ae84774f3...
  [STAGE 02/19] PASS: Notice Intake & Rule-Based Action Extraction - 3 actions extracted
  [STAGE 03/19] PASS: Action Categorization & Amount Parsing - Fee ₹350, Consent Slip, Materials
  [STAGE 04/19] PASS: Notice Fingerprint Deduplication - Duplicate forward replayed existing actions
  [STAGE 05/19] PASS: Deadline Normalization (IST +05:30) - Deadline: 2026-09-18T17:00:00+05:30
  [STAGE 06/19] PASS: Action Deadline Patch & Audit Log - Updated to 2026-09-25T17:00:00+05:30
  [STAGE 07/19] PASS: Reminder Draft Creation - Drafted for 2026-09-25T17:00:00+05:30
  [STAGE 08/19] PASS: Human Authority Gate (HTTP 403) - Blocked non-parent autonomous approval
  [STAGE 09/19] PASS: Parent Authorization Gate - Approved, new version v3
  [STAGE 10/19] PASS: Action Completion Transition - Status: completed, version: 4
  [STAGE 11/19] PASS: Optimistic Concurrency Conflict - Rejected stale mutation with 409
  [STAGE 12/19] PASS: Workspace Capacity Limit (50 Max) - Rejected 51st notice with 409
  [STAGE 13/19] PASS: Cross-Workspace Isolation - Tenant B cannot view Tenant A notice (404)
  [STAGE 14/19] PASS: Idempotency-Key Replay - Exact replay cached and returned
  [STAGE 15/19] PASS: Idempotency Conflict Detection - Altered payload rejected with 409
  [STAGE 16/19] PASS: Malformed Payload Rejection - HTTP 422 validation response
  [STAGE 17/19] PASS: Extractor Failure Handling - HTTP 503 EXTRACTOR_UNAVAILABLE
  [STAGE 18/19] PASS: Truthful Health & Readiness Probes - Status: ok, DB: sqlite
  [STAGE 19/19] PASS: Privacy & Zero Personal Spend Guarantee - Zero paid APIs (₹0.00 spend), minimal child alias only
===========================================================================
  ALL 19/19 STAGES PASSED SUCCESSFULLY!
===========================================================================
```

---

## 4. Static Analysis & Linting

- **Ruff Linter**: `All checks passed!` (0 errors)
- **Ruff Formatter**: `26 files already formatted` (0 reformats needed)
- **Mypy Type Checker**: `Success: no issues found in 26 source files` (0 errors)
- **ESLint**: `0 warnings, 0 errors`
- **TypeScript Compiler (`tsc`)**: `0 errors`
