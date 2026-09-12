# SB-003 Acceptance: Strands Agent Advisory Loop, Bounded Tools & Inference Admission Safety

- **Task ID**: `SB-003`
- **Worker**: AGY (Senior Full-Stack Developer)
- **Branch**: `worker/agy/SB-003`
- **Base**: `worker/agy/SB-002` (Commit `77750c5`)
- **Status**: COMPLETE & VERIFIED
- **Total Personal Spend**: **₹0.00 / $0.00**
- **External Paid APIs**: **None (Zero paid cloud APIs; Groq free tier / offline mock transport)**

---

## 1. Executive Summary

Milestone `SB-003` incorporates the **Strands Agents** integration seam into Project 3 (Schoolbag). The system provides an AI-augmented advisory loop using `openai/gpt-oss-20b` while strictly maintaining our foundational safety invariants:
1. **Zero Personal Spend**: $0.00 / ₹0.00 personal spend; zero paid provider calls; free tier and offline test transport.
2. **Single Read-Only Bounded Tool**: The agent interacts solely through `get_school_notice_context`. The model has zero capability to mutate database records, execute financial transactions, autosign consent forms, or perform arbitrary outbound network calls.
3. **Atomic Inference Admission Safety**: Atomic single-active concurrency locks, multi-tier rolling window rate limits (6 req/60s, 120 req/24h), 15-minute 429 provider backoff cooldown, and zero-send idempotent response caching.
4. **Mandatory Human Authority Gate**: Any suggested action involving monetary fees or parental consent is strictly overridden to `approval_required: True`. Non-parent attempts to approve actions receive HTTP 403 `HUMAN_APPROVAL_REQUIRED`.
5. **Observed Tool Execution Grounding**: Any model completion generated without observed execution of the bounded tool is rejected with HTTP 502 `ASSISTANT_INVALID_OUTPUT`.
6. **Privacy Boundary**: Comprehensive PII scrubber scrubs phone numbers, emails, student registration IDs, Aadhaar numbers, and DOB before model dispatch.

---

## 2. Implemented Architecture & Seams

### 2.1 Strands Agent Advisory Engine (`strands_agent.py`)
- **Integration Seam**: Utilizes `strands-agents[openai]==1.54.0` pattern.
- **Two-Stage Loop**:
  - **Stage 1 (Tool Loop)**: Prompt instructs the agent to inspect the notice via `get_school_notice_context`. Tool execution is verified and logged.
  - **Stage 2 (Extraction & Validation)**: Structured extraction schema parsed into `StrandsAdvisoryResponse`.
- **Grounded Verification**:
  - Validates that `actual_tools >= 1`.
  - Rejects completions without tool execution (`ASSISTANT_INVALID_OUTPUT`).
  - Restricts action categories to valid set (`fee`, `consent`, `materials`, `exam`, `general`).
  - Enforces mandatory human approval on all fees and consent items.

### 2.2 Bounded Read-Only Context Tool
- **`get_school_notice_context`**:
  - Accepts notice ID and reads sanitized notice metadata and child context.
  - Read-only execution with zero mutation capabilities.
  - Parameter resilience: defaults safely when mock arguments are omitted.

### 2.3 Atomic Inference Admission Control (`admission.py`)
- **Storage Layer**: SQLite / PostgreSQL `inference_admissions` table with atomic transaction isolation.
- **Single-Active Concurrency Lock**: Only 1 active inference request permitted per workspace. Concurrent requests fail immediately with HTTP 429 `ASSISTANT_BUSY`.
- **Multi-Tier Sliding Rate Limits**:
  - Max 6 requests per 60 seconds rolling window.
  - Max 120 requests per 24 hours rolling window.
  - Max 24 successful completions per 24 hours.
- **Provider 429 Backoff**:
  - On receiving provider 429, records failure code and locks admissions for 15 minutes.
- **Zero-Send Idempotent Caching**:
  - Computes `request_key_hash` and `payload_hash`.
  - Exact replays return the cached response with `provenance["cached"] = True` and 0 additional model sends.

### 2.4 Groq Free-Tier / Offline Model Adapter (`groq_model.py`)
- **Target Model**: `openai/gpt-oss-20b` (Groq OpenAI-compatible free tier endpoint).
- **Sticky Send Budget**: Enforces a strict maximum of 6 network sends per request session.
- **Deadline Enforcement**: 15-second total timeout envelope (`AssistantTimeoutError` -> HTTP 504).
- **HTTPS Target Verification**: Enforces secure HTTPS URL endpoint validation.
- **Offline Mock Transport**: Supports `httpx.MockTransport` for 100% deterministic, zero-cost unit and integration tests.

### 2.5 Privacy Protection & PII Scrubber (`redaction.py`)
- Regex-based pre-inference redaction pipeline:
  - Phone numbers (Indian 10-digit mobile, +91, with spaces/hyphens) -> `[PHONE REDACTED]`
  - Email addresses -> `[EMAIL REDACTED]`
  - Student IDs / Roll numbers -> `[STUDENT ID REDACTED]`
  - Aadhaar / National IDs -> `[AADHAAR REDACTED]`
  - Dates of Birth -> `[DOB REDACTED]`
- Minimal child identifiers: preserves only child alias (`Kavya`, `Arun`) and grade (`Class 5-B`).

### 2.6 Frontend Strands Advisory UI
- **`NoticeCard.tsx`**:
  - Added "Analyze with Strands AI" trigger button with spinner.
  - Renders Strands Advisory Result panel:
    - Urgency badge: `Urgent Priority` vs `Standard Priority`
    - Model attribution badge: `Strands AI (openai/gpt-oss-20b)`
    - Summary and advisory notes
    - Suggested action drafts list with fee amounts, deadlines, and explicit `Advisory Draft - Requires Human Parent Approval` warning
    - Bounded tool and admission safety declarations
  - Renders warning banner on HTTP 429 / 503 / 409 errors.
- **`ProvenanceCard.tsx`**:
  - Added Strands Agent Engine declaration with bounded tool disclosure and rate limit metrics.
- **`Header.tsx`**:
  - Upgraded Evaluator Tour sequence with Step 2b for Strands AI analysis.
  - Updated version badge to `v0.3.0`.

---

## 3. Verification Matrix

| Verification Check | Target | Result | Evidence |
| :--- | :--- | :--- | :--- |
| **Backend Pytest Suite** | 34 tests across 8 suites | **34/34 PASS (100%)** | `pytest -v` (15.4s) |
| **Strands Advisory Suite** | 12 dedicated agent tests | **12/12 PASS (100%)** | `test_strands_advisory.py` |
| **Frontend Vitest Suite** | 8 component & workflow tests | **8/8 PASS (100%)** | `npm test -- --run` (2.28s) |
| **20-Stage Release Smoke** | Full lifecycle + Strands Stage 20 | **20/20 PASS (100%)** | `release_smoke.py` |
| **Python Code Quality** | `ruff check src tests` | **PASS (0 errors)** | Clean ruff check |
| **Python Formatting** | `ruff format --check src tests` | **PASS (0 diffs)** | 32 files formatted |
| **Static Type Checking** | `mypy src` | **PASS (0 errors)** | 22 source files verified |
| **Frontend Linting** | `eslint . --max-warnings 0` | **PASS (0 warnings)** | Clean eslint |
| **Frontend Build** | `tsc && vite build` | **PASS (0 errors)** | Dist bundle generated |

---

## 4. Program Invariant Guarantees

1. **Zero Spend Guarantee**:
   - Total expenditures: **₹0.00 / $0.00**.
   - Zero paid cloud API keys or billable endpoints configured.
2. **Untouched Other Repos**:
   - `01_BORROWED_STEPS`: Untouched.
   - `02_BENCHBOOK`: Untouched.
   - `00_PROGRAM_CONTROL`: Untouched.
3. **Child Privacy**:
   - Zero real student records; only synthetic alias (`Kavya`, `Arun`).
   - PII scrubbing verified in automated test suite.
4. **Human Authority Gate**:
   - Model outputs are strictly advisory drafts.
   - Non-parent execution remains permanently blocked with HTTP 403 `HUMAN_APPROVAL_REQUIRED`.
