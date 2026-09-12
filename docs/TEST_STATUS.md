# Schoolbag Test Status & Verification Report

- Date: September 2026
- Branch: `worker/agy/SB-004`
- Total Spend: **₹0.00 / $0.00**
- External Paid APIs: **Zero (Free Groq OpenAI endpoint / Offline mock transport / Local RFC 5545 generator)**

---

## 1. Backend Pytest Suite (`services/school_service/tests/`)

- Total Tests: **37**
- Passed: **37**
- Failed: **0**
- Execution Time: **16.51s**

| Test File | Tests | Status | Scope |
| :--- | :--- | :--- | :--- |
| `test_workflow_slice.py` | 1 | **PASSED** | Complete 9-step vertical slice: workspace session, intake, 2+ action extraction, deduplication, deadline normalizer, reminder draft, 403 assistant rejection, parent approval & completion persistence, 422 & 503 failures |
| `test_calendar_export.py` | 3 | **PASSED** | Single-action RFC 5545 `.ics` formatting, UTC timestamp conversion, -2h `VALARM` reminder, workspace aggregate family feed, HTTP endpoints |
| `test_config_and_security.py` | 4 | **PASSED** | Production environment detector, nosniff/DENY security headers, production origin enforcement (403 ORIGIN_REFUSED), preset catalog integrity |
| `test_workspace_isolation.py` | 3 | **PASSED** | Session cookie issuance, cross-workspace 404 isolation, 50-notice workspace capacity enforcement |
| `test_deduplication.py` | 4 | **PASSED** | Whitespace/case normalization resilience, Idempotency-Key replay, 409 conflict on altered payload, header vs body mismatch |
| `test_human_approval.py` | 2 | **PASSED** | Assistant 403 rejection on fees and consent, parent approval, optimistic concurrency locking 409 conflict |
| `test_deadline_normalizer.py` | 3 | **PASSED** | ISO timestamp preservation, YYYY-MM-DD date normalization, relative weekday and urgent parsing in IST (+05:30) |
| `test_fullstack_packaging.py` | 3 | **PASSED** | `/api/health` and `/api/ready` disclosures, strict JSON 404 for unknown `/api/*`, static SPA serving and fallback |
| `test_transactional_concurrency.py` | 2 | **PASSED** | Full workflow slice on real ephemeral PostgreSQL 16.10, two-connection concurrent optimistic conflict |
| `test_strands_advisory.py` | 12 | **PASSED** | Two-stage Strands loop, PII scrubbing (phone, email, student ID, Aadhaar, DOB), ungrounded category rejection, mandatory human approvals, idempotent replay, version conflict (409), send budget (6), 429 cooldown, connection failure (503), hallucination without tool (502), missing key, full HTTP E2E |

---

## 2. Frontend Vitest Suite (`apps/web/src/test/`)

- Total Tests: **10**
- Passed: **10**
- Failed: **0**
- Execution Time: **2.45s**

| Test Case | Status | Verified Functionality |
| :--- | :--- | :--- |
| `renders evaluator guide, zero spend declaration, and minimal identifier guarantee` | **PASSED** | Header badges, task ID, zero spend disclosure, capacity badge, child filters |
| `renders action card with normalized deadline and human gate demonstration button` | **PASSED** | Action card layout, amount chip, IST deadline, approval buttons |
| `handles simulated assistant approval rejection with HTTP 403 error banner` | **PASSED** | Assistant approval triggers 403 and displays prominent red rejection banner |
| `renders notice card with synthetic metadata and child context` | **PASSED** | Notice card source type, child alias chip, class chip |
| `renders audit event stream with security rejection event` | **PASSED** | Immutable event stream displaying `approval_rejected_human_gate` and notes |
| `renders provenance card with truthful disclosures and Strands agent seam` | **PASSED** | Truthful engine disclosure, Strands Agent disclosure, Kovai Vidya Mandir provenance, ₹0.00 spend |
| `triggers Strands AI analysis on notice card and renders advisory drafts with human gate notice` | **PASSED** | Strands advisory loading state, summary, urgency status, suggested action drafts with human gate notice, bounded tool declaration |
| `handles Strands AI rate limiting error 429 ASSISTANT_BUSY with warning banner` | **PASSED** | Rate limiting error mapping and warning banner display on NoticeCard |
| `renders .ics export button and WhatsApp draft copy button on action card` | **PASSED** | Export .ics trigger, WhatsApp reminder draft formatted copy to clipboard and toast |
| `renders Family Weekly Board with multi-child columns, pending fee total, and overlap alert` | **PASSED** | Visual diary layout, Kavya and Arun column grouping, ₹550 pending fee computation, overlap detection alert |

---

## 3. 22-Stage Release Smoke Suite (`scripts/release_smoke.py`)

- Total Stages: **22**
- Passed: **22**
- Failed: **0**

```
===========================================================================
  SCHOOLBAG (SB-001 - SB-004) - 22-STAGE END-TO-END RELEASE SMOKE SUITE
===========================================================================
  [STAGE 01/22] PASS: Workspace Session Cookie Issuance - ws_id=ws_8852834fe...
  [STAGE 02/22] PASS: Notice Intake & Rule-Based Action Extraction - 3 actions extracted
  [STAGE 03/22] PASS: Action Categorization & Amount Parsing - Fee ₹350, Consent Slip, Materials
  [STAGE 04/22] PASS: Notice Fingerprint Deduplication - Duplicate forward replayed existing actions
  [STAGE 05/22] PASS: Deadline Normalization (IST +05:30) - Deadline: 2026-09-18T17:00:00+05:30
  [STAGE 06/22] PASS: Action Deadline Patch & Audit Log - Updated to 2026-09-25T17:00:00+05:30
  [STAGE 07/22] PASS: Reminder Draft Creation - Drafted for 2026-09-25T17:00:00+05:30
  [STAGE 08/22] PASS: Human Authority Gate (HTTP 403) - Blocked non-parent autonomous approval
  [STAGE 09/22] PASS: Parent Authorization Gate - Approved, new version v3
  [STAGE 10/22] PASS: Action Completion Transition - Status: completed, version: 4
  [STAGE 11/22] PASS: Optimistic Concurrency Conflict - Rejected stale mutation with 409
  [STAGE 12/22] PASS: Workspace Capacity Limit (50 Max) - Rejected 51st notice with 409
  [STAGE 13/22] PASS: Cross-Workspace Isolation - Tenant B cannot view Tenant A notice (404)
  [STAGE 14/22] PASS: Idempotency-Key Replay - Exact replay cached and returned
  [STAGE 15/22] PASS: Idempotency Conflict Detection - Altered payload rejected with 409
  [STAGE 16/22] PASS: Malformed Payload Rejection - HTTP 422 validation response
  [STAGE 17/22] PASS: Extractor Failure Handling - HTTP 503 EXTRACTOR_UNAVAILABLE
  [STAGE 18/22] PASS: Truthful Health & Readiness Probes - Status: ok, DB: sqlite
  [STAGE 19/22] PASS: Privacy & Zero Personal Spend Guarantee - Zero paid APIs (₹0.00 spend), minimal child alias only
  [STAGE 20/22] PASS: Strands Agent Advisory Loop & Bounded Read Tool - Grounded against get_school_notice_context with mandatory human approval & idempotency
  [STAGE 21/22] PASS: Action RFC 5545 iCalendar (.ics) Export - Valid VCALENDAR/VEVENT with -2h alarm reminder trigger and UTC format
  [STAGE 22/22] PASS: Workspace Aggregate Family Calendar Feed (.ics) - Multi-child schedule export (3 events in VCALENDAR)
===========================================================================
  ALL 22/22 STAGES PASSED SUCCESSFULLY!
===========================================================================
```
