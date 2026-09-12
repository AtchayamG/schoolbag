# Schoolbag Architecture & System Design

## 1. Product Vision

**Schoolbag** is an agentic assistant for families designed to turn chaotic school communication (WhatsApp forward chains, school circular PDFs, diary notes, and portal emails) into the few actionable items a family actually needs to do:
- Fee payments
- Consent slips & field trip permissions
- Required classroom materials & supplies
- Exam and academic milestones

Schoolbag enforces strict boundaries: it **never** signs consent, spends money, or dispatches external communications automatically. Every suggested reminder, payment, or consent action is visibly a **DRAFT** requiring human parent approval.

---

## 2. Core Architectural Principles & Boundaries

1. **Zero Personal Spend (\$0.00 / ₹0.00)**:
   - Uses a deterministic rule-based extractor with confidence scoring and explicit synthetic disclosure.
   - Requires zero paid external API subscriptions or cloud keys.

2. **Strict Human Authority Gate (HTTP 403)**:
   - Automated agents, background assistants, and bots are strictly blocked from approving actions requiring parent authorization (`HUMAN_APPROVAL_REQUIRED`, HTTP 403).
   - Only actors authenticated with role `parent` can authorize payments or sign consent slips.

3. **Privacy-Preserving Minimal Identifiers**:
   - Stores only child aliases (e.g., `Kavya`, `Arun`) and class/section identifiers (e.g., `Class 5-B`).
   - Strictly refuses to store or require student IDs, dates of birth (DOB), medical records, home addresses, or parent Aadhaar/PAN details.

4. **Multi-Tenant Workspace Isolation**:
   - Every user receives a secure 32-byte session token mapped to an isolated workspace.
   - Cross-workspace data access returns HTTP 404 `NOTICE_NOT_FOUND` / `NOT_FOUND`.
   - Workspaces enforce a hard capacity limit of 50 notices per workspace (HTTP 409 `CAPACITY_EXCEEDED`).

5. **Deterministic IST Deadline Normalization**:
   - Dates and relative phrases ("Friday 5 PM", "Tomorrow 10 AM", "Urgent today", "Next Thursday") are deterministically normalized into Indian Standard Time (+05:30) ISO-8601 timestamps.

6. **Dual-Engine Storage Architecture**:
   - Thread-safe storage layer supporting SQLite WAL for instant zero-dependency local development and ephemeral PostgreSQL 16 for production containerized workloads.

---

## 3. Workflow Pipeline

```
[Raw Notice Intake]
         │
         ▼
[SHA-256 Fingerprint Deduplication]
    ├── If Duplicate ──> [Replay Existing Actions (200 OK)]
    └── If New Notice
         │
         ▼
[Action Extraction Engine]
  - Categorization (Fees, Consent, Materials, Exams)
  - Provenance & Confidence Scoring (advisory_only: true)
  - Deadline Normalization (IST +05:30)
         │
         ▼
[Draft Reminder Creation]
  - Calendar / In-App / Email / Push
         │
         ▼
[Human Authority Gate]
    ├── If Assistant / Bot ──> [HTTP 403 HUMAN_APPROVAL_REQUIRED]
    └── If Parent ────────────> [HTTP 200 OK -> Approved]
                                        │
                                        ▼
                                 [Mark Completed]
```

---

## 4. Security & Concurrency Controls

- **Optimistic Concurrency Control**:
  - Every action mutation enforces `expected_version`. If a concurrent update has occurred, the request is rejected with HTTP 409 `STATE_CONFLICT`.
- **Idempotency Protection**:
  - `Idempotency-Key` headers cache responses. Exact re-submissions return cached payloads; submissions with identical keys but altered payloads are rejected with HTTP 409 `IDEMPOTENCY_CONFLICT`.
- **Append-Only Audit Stream**:
  - All state transitions (`notice_ingested`, `action_extracted`, `approval_rejected_human_gate`, `action_approved_by_parent`, `deadline_updated`, `action_completed`, `reminder_drafted`) are immutably logged with actor attribution and timestamps.
