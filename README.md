# Schoolbag (Project 3)

> **Turns scattered school messages into the few things a family needs to do.**

Schoolbag is an agentic family assistant that ingests messy school communications (WhatsApp forward chains, school circular PDFs, diary notes, and portal emails) and extracts structured, actionable items:
- Fee payments (with parsed amounts)
- Consent slips & excursion permissions
- Required materials & classroom pack items
- Exam milestones & timetable prep

---

## Safety & Architectural Guardrails

1. **Strict Human Authority Gate**:
   - Schoolbag **never** signs consent, spends money, or dispatches external communications automatically.
   - Non-parent actors (e.g. `assistant`, background AI bots) attempting to authorize actions receive an immediate **HTTP 403 `HUMAN_APPROVAL_REQUIRED`**.
   - Every suggested payment or consent slip is visibly a **DRAFT** requiring explicit human parent authorization.

2. **Privacy-Preserving Minimal Identifiers**:
   - Only stores privacy-safe child aliases (e.g., `Kavya`, `Arun`) and class/section identifiers (e.g., `Class 5-B`).
   - Strictly refuses to store or require student IDs, dates of birth (DOB), medical records, or parent identity documents.

3. **Zero Personal Spend (\$0.00 / ₹0.00)**:
   - Uses a deterministic, rule-based extraction engine with confidence scoring and explicit synthetic disclosure.
   - Operates with zero paid cloud API calls and zero secrets in source.

4. **Deterministic IST Deadline Normalization**:
   - Dates and relative expressions ("Friday 5 PM", "Tomorrow 10 AM", "Urgent today") are calculated deterministically in Indian Standard Time (`+05:30`).

5. **Content Deduplication & Idempotency**:
   - Whitespace- and casing-normalized SHA-256 fingerprinting prevents re-ingestion of repeated WhatsApp forwards.
   - Full support for `Idempotency-Key` headers prevents duplicate action creation.

6. **Dual-Engine Storage**:
   - Thread-safe storage layer supporting SQLite WAL for zero-dependency local development and ephemeral PostgreSQL 16 for production deployment.

---

## Tamil Nadu School Scenario

Schoolbag includes believable synthetic presets modeling an English-first school scenario in Tamil Nadu:
- **School**: Kovai Vidya Mandir, RS Puram, Coimbatore
- **Children**: Kavya (Class 5-B) & Arun (Class 8-A)
- **Presets**:
  1. *Annual Day Field Trip to Ooty & Costume Fee*: ₹350 costume fee by Friday 5 PM + signed field trip consent form + chart paper & clay models.
  2. *Science Fair Materials*: Chart paper, clay, craft supplies for exhibition.
  3. *Mid-Term Exam Schedule*: Mathematics & Science timetable and hall ticket signatures.

---

## Quick Start

### Prerequisites
- Python 3.11+ (or Python 3.14 via `uv`)
- Node.js v20+ & npm

### 1. Run 19-Stage Release Smoke Verification
```bash
cd services/school_service
.\.venv\Scripts\python.exe ..\..\scripts\release_smoke.py
```
*Expected Output*: `ALL 19/19 STAGES PASSED SUCCESSFULLY!`

### 2. Run Backend Test Suite (Pytest)
```bash
cd services/school_service
.\.venv\Scripts\python.exe -m pytest -v
```
*Expected Output*: `18 passed in ~14s` (including real ephemeral PostgreSQL 16 tests).

### 3. Run Frontend Test Suite (Vitest)
```bash
cd apps/web
npm test -- --reporter=dot
```
*Expected Output*: `6 passed (1 file)`.

### 4. Build Production Frontend Bundle
```bash
cd apps/web
npm run build
```

### 5. Launch Interactive Browser Review Server
```bash
cd 03_SCHOOLBAG
.\services\school_service\.venv\Scripts\python.exe scripts\browser_review_server.py --port 8000
```
Open **http://127.0.0.1:8000** in your web browser:
- Use the **Evaluator Guide** banner to verify guardrails.
- Click **"Ingest School Notice"** to select a synthetic preset for Kovai Vidya Mandir.
- Click **"Simulate Assistant Approval (Expect 403)"** to observe the Human Authority Gate rejection banner in real time.
- Click **"Parent Sign & Authorize"** to approve the action.
- Observe the immutable **Audit Event Log** recording every transition.

---

## Quality Metrics

- **Backend Pytest**: 18/18 passed
- **Frontend Vitest**: 6/6 passed
- **Release Smoke**: 19/19 stages passed
- **Ruff Linting**: Clean (0 errors)
- **Ruff Formatting**: Clean (26 files formatted)
- **Mypy Type Checking**: Clean (0 errors across 26 files)
- **ESLint**: Clean (0 warnings, 0 errors)
- **TypeScript**: Clean (0 errors)
