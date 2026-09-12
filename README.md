# Schoolbag (Project 3) — Everyday AI Family School Assistant

> **Turns scattered school WhatsApp forwards and circulars into clear, parent-authorized family actions and calendar events.**

Schoolbag is an agentic family assistant built for school-going households (especially multi-child families) that ingests messy school communications (WhatsApp forward chains, school circular PDFs, diary notes, and portal emails) and extracts structured, actionable obligations:
- 💳 **Fee payments** (with exact amounts parsed in Indian Rupees ₹ INR)
- 📝 **Consent slips & excursion permissions** (field trips, sports events)
- 📦 **Required materials & classroom pack items** (craft materials, uniforms)
- 🎓 **Exam milestones & timetable prep** (hall tickets, revision schedules)
- 📅 **Household Calendar Export** (RFC 5545 `.ics` with -2h alarm reminders)
- 💬 **WhatsApp Family Reminder Drafting** (1-click formatted copy to clipboard)
- 📖 **Family Weekly Board** (Visual school diary with multi-child side-by-side view & deadline overlap alerts)

---

## Safety & Architectural Guardrails

1. **Strict Human Authority Gate**:
   - Schoolbag **never** signs consent, spends money, or dispatches external communications automatically.
   - Non-parent actors (e.g. `assistant`, background AI bots) attempting to authorize actions receive an immediate **HTTP 403 `HUMAN_APPROVAL_REQUIRED`**.
   - Every suggested payment or consent slip is visibly a **DRAFT** requiring explicit human parent authorization.

2. **Strands Agent Advisory Loop with Bounded Read Tool**:
   - Implements a two-stage advisory loop using the `strands-agents[openai]==1.54.0` pattern with open-source models (`openai/gpt-oss-20b`).
   - The agent is grounded against a single read-only tool: `get_school_notice_context`. The model has **zero** capability to mutate database records, execute transactions, or perform arbitrary network calls.
   - Grounding verification: Completions generated without observed execution of the tool are rejected with **HTTP 502 `ASSISTANT_INVALID_OUTPUT`**.

3. **Atomic Inference Admission Safety**:
   - Atomic single-active concurrency lock: only 1 active inference request per workspace (HTTP 429 `ASSISTANT_BUSY`).
   - Multi-tier sliding rate limits: max 6 requests per 60s, 120 requests per 24h, 24 completions per 24h.
   - Provider 429 cooldown: 15-minute lock on admissions after provider backoff.
   - Zero-send idempotent caching: identical payloads return cached results with 0 extra model calls.

4. **Privacy-Preserving Minimal Identifiers & PII Redaction**:
   - Only stores privacy-safe child aliases (e.g., `Kavya`, `Arun`) and class/section identifiers (e.g., `Class 5-B`).
   - Pre-inference regex redaction pipeline automatically strips phone numbers (+91, 10-digit), emails, student IDs, Aadhaar numbers, and DOB before model dispatch.
   - Strictly refuses to store or require student IDs, dates of birth (DOB), medical records, or parent identity documents.

5. **Zero Personal Spend ($0.00 / ₹0.00)**:
   - Operates with strictly $0.00 / ₹0.00 personal spend using deterministic rule extractors, free-tier Groq model adapters, and offline mock transports.
   - Zero secrets stored in source.

6. **Deterministic IST Deadline Normalization**:
   - Dates and relative expressions ("Friday 5 PM", "Tomorrow 10 AM", "Urgent today") are calculated deterministically in Indian Standard Time (`+05:30`).

7. **RFC 5545 iCalendar Interoperability**:
   - Single-action (`GET /api/actions/{id}/calendar.ics`) and aggregate workspace feed (`GET /api/actions/calendar.ics`).
   - Universal UTC `Z` formatting with `X-WR-TIMEZONE:Asia/Kolkata` and -2h `VALARM` audio/display reminder triggers.

8. **Content Deduplication & Idempotency**:
   - Whitespace- and casing-normalized SHA-256 fingerprinting prevents re-ingestion of repeated WhatsApp forwards.
   - Full support for `Idempotency-Key` headers prevents duplicate action creation.

9. **Dual-Engine Storage**:
   - Thread-safe storage layer supporting SQLite WAL for zero-dependency local development and ephemeral PostgreSQL 16 for production deployment.

---

## Tamil Nadu School Scenarios

Schoolbag includes believable synthetic presets modeling an English-first school scenario in Tamil Nadu:
- **School**: Kovai Vidya Mandir, RS Puram, Coimbatore
- **Children**: Kavya (Class 5-B) & Arun (Class 8-A)
- **Presets**:
  1. *Annual Day Field Trip to Ooty & Costume Fee*: ₹350 costume fee by Friday 5 PM + signed field trip consent form + chart paper & clay models.
  2. *Science Fair Materials*: Chart paper, clay, craft supplies for exhibition.
  3. *Mid-Term Exam Schedule*: Mathematics & Science timetable and hall ticket signatures.
  4. *Annual Sports Meet at Nehru Stadium*: ₹200 bus transport fee + signed athletic consent slip for Arun (Class 8-A).

---

## Quick Start

### Prerequisites
- Python 3.11+ (or Python 3.14 via `uv`)
- Node.js v20+ & npm

### 1. Run 22-Stage Release Smoke Verification
```bash
cd services/school_service
.\.venv\Scripts\python.exe ..\..\scripts\release_smoke.py
```
*Expected Output*: `ALL 22/22 STAGES PASSED SUCCESSFULLY!`

### 2. Run 11-Stage Live Canary Evaluator
```bash
cd 03_SCHOOLBAG
.\services\school_service\.venv\Scripts\python.exe scripts\live_canary.py
```
*Expected Output*: `ALL 11 CANARY STAGES PASSED SUCCESSFULLY!`

### 3. Run Backend Test Suite (Pytest)
```bash
cd services/school_service
.\.venv\Scripts\python.exe -m pytest -v
```
*Expected Output*: `37 passed in ~16.5s` (including Strands agent tests, calendar export, and real ephemeral PostgreSQL 16 tests).

### 4. Run Frontend Test Suite (Vitest)
```bash
cd apps/web
cmd.exe /c npm test -- --run
```
*Expected Output*: `10 passed (1 file)`.

### 5. Build Production Frontend Bundle
```bash
cd apps/web
cmd.exe /c npm run build
```

### 6. Launch Interactive Browser Review Server
```bash
cd 03_SCHOOLBAG
.\services\school_service\.venv\Scripts\python.exe scripts\browser_review_server.py --port 8000
```
Open **http://127.0.0.1:8000** in your web browser:
- Use the **Evaluator Guide** banner (`v0.5.0`) to follow the 60-second verification walkthrough.
- Click **"Ingest School Notice"** to select a synthetic preset for Kovai Vidya Mandir.
- Click **"Analyze with Strands AI"** to observe the bounded tool advisory loop.
- Click **"Simulate Assistant Approval (Expect 403)"** to observe the Human Authority Gate rejection banner in real time.
- Click **"Parent Sign & Authorize"** to approve the action.
- Click **"Export .ics"** or **"WhatsApp Draft"** to test calendar export and family coordination.
- Switch to **"Family Weekly Board (Visual Diary)"** to review the multi-child side-by-side view, pending fee totals, and overlap alerts.

---

## Quality & Test Metrics

- **Backend Pytest**: 37/37 passed (100%)
- **Frontend Vitest**: 10/10 passed (100%)
- **Release Smoke**: 22/22 stages passed (100%)
- **Live Canary**: 11/11 stages passed (100%)
- **Ruff Linting**: Clean (0 errors across 37 files)
- **Ruff Formatting**: Clean (37 files formatted)
- **ESLint**: Clean (0 warnings, 0 errors)
- **TypeScript**: Clean (0 errors)
- **Personal Spend**: **₹0.00 / $0.00**
