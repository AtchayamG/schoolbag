# Schoolbag Review Queue

## Review Items for Evaluator

1. **Human Authority Gate Demonstration**:
   - Location: `apps/web/src/components/ActionCard.tsx`
   - Test File: `services/school_service/tests/test_human_approval.py`
   - Verification: In the web workbench, click "Simulate Assistant Approval (Expect 403)". The app sends `actor_type: "assistant"` to `/api/actions/{id}/approve`, which raises `HumanApprovalRequiredError` and returns HTTP 403 `HUMAN_APPROVAL_REQUIRED`.

2. **Deduplication Resilience**:
   - Location: `services/school_service/src/schoolbag/domain/workflow.py` (`compute_notice_fingerprint`)
   - Test File: `services/school_service/tests/test_deduplication.py`
   - Verification: Repeated notices with minor whitespace or casing differences generate identical SHA-256 fingerprints, returning existing action items with `is_deduplicated: true` and 0 duplicated records in the database.

3. **IST Deadline Normalization**:
   - Location: `services/school_service/src/schoolbag/infrastructure/normalizer.py`
   - Test File: `services/school_service/tests/test_deadline_normalizer.py`
   - Verification: Parses relative expressions ("Friday 5 PM", "Tomorrow 10 AM", "Urgent today", "2026-09-25") deterministically to ISO-8601 strings with `+05:30` offset.

4. **Dual-Database Support & Ephemeral PostgreSQL Testing**:
   - Location: `services/school_service/src/schoolbag/infrastructure/database.py` & `sqlite_store.py`
   - Test File: `services/school_service/tests/test_transactional_concurrency.py`
   - Verification: Runs the full workflow slice and concurrent optimistic locking contention against a real ephemeral PostgreSQL 16 cluster launched dynamically on loopback.

5. **Privacy & Zero Personal Spend**:
   - Location: `services/school_service/src/schoolbag/infrastructure/seed_data.py` & `extractor.py`
   - Presets: Synthetic school scenarios for *Kovai Vidya Mandir, Coimbatore*.
   - Verification: Minimal child identifiers only (`Kavya`, `Arun`). Zero DOB, zero medical records, zero student IDs. Zero paid API calls.
