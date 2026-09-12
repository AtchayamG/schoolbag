# Schoolbag Review Queue

## Review Items for Evaluator (SB-001, SB-002 & SB-003)

1. **Strands Agent Advisory Loop & Bounded Read Tool (SB-003)**:
   - Location: `services/school_service/src/schoolbag/infrastructure/strands_agent.py` & `apps/web/src/components/NoticeCard.tsx`
   - Test File: `services/school_service/tests/test_strands_advisory.py`
   - Verification: In the web workbench, click "Analyze with Strands AI" on any notice card. Strands Agent invokes `get_school_notice_context` to inspect the notice, performs extraction, forces human approval on fee/consent items, and surfaces draft suggestions with truthful model provenance (`openai/gpt-oss-20b`).

2. **Atomic Inference Admission Control (SB-003)**:
   - Location: `services/school_service/src/schoolbag/infrastructure/admission.py`
   - Test File: `services/school_service/tests/test_strands_advisory.py`
   - Verification: Single-active atomic lock prevents concurrent inferences (HTTP 429), sliding window limits requests to 6/60s and 120/24h, 15-minute cooldown on 429 provider backoff, and idempotent replay avoids duplicate LLM calls.

3. **PII Pre-Inference Scrubbing (SB-003)**:
   - Location: `services/school_service/src/schoolbag/infrastructure/redaction.py`
   - Test File: `services/school_service/tests/test_strands_advisory.py`
   - Verification: Phone numbers, emails, student registration IDs, Aadhaar numbers, and DOB are redacted before dispatch to the model, preserving only minimal child alias (`Kavya`, `Arun`).

4. **Human Authority Gate Demonstration (SB-001)**:
   - Location: `apps/web/src/components/ActionCard.tsx`
   - Test File: `services/school_service/tests/test_human_approval.py`
   - Verification: In the web workbench, click "Simulate Assistant Approval (Expect 403)". The app sends `actor_type: "assistant"` to `/api/actions/{id}/approve`, which raises `HumanApprovalRequiredError` and returns HTTP 403 `HUMAN_APPROVAL_REQUIRED`.

5. **Security Headers & Production Origin Enforcement (SB-002)**:
   - Location: `services/school_service/src/schoolbag/interfaces/http/app.py` (`SecurityMiddleware`) & `session.py` (`validate_production_request`)
   - Test File: `services/school_service/tests/test_config_and_security.py`
   - Verification: Responses enforce `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`. In production, unlisted external origins on mutation requests receive HTTP 403 `ORIGIN_REFUSED`.

6. **Zero-Spend Cloud Deployment Packaging (SB-002)**:
   - Manifests: `03_SCHOOLBAG/render.yaml` (Render Free Docker web service with `/api/health`) and `03_SCHOOLBAG/vercel.json` (Vercel Hobby static web + reverse proxy).
   - Verification: Both configs use ₹0.00 / $0.00 spend and zero credentials.

7. **Expanded Tamil Nadu Presets (SB-002)**:
   - Location: `services/school_service/src/schoolbag/infrastructure/seed_data.py`
   - Scenarios: Added 4th scenario (`preset-sports-day` - Annual Inter-School Athletics Meet at Nehru Stadium, Coimbatore, Class 8-A Arun, ₹200 fee, consent form).

8. **Evaluator Walkthrough Tour Banner (SB-002 & SB-003)**:
   - Location: `apps/web/src/components/Header.tsx`
   - Verification: Interactive "60-Second Evaluator Tour" collapsible guide, displaying version `v0.3.0` badge and step-by-step verification instructions.

9. **Deduplication Resilience & IST Deadline Normalization**:
   - Locations: `schoolbag/domain/workflow.py`, `schoolbag/infrastructure/normalizer.py`
   - Test Files: `test_deduplication.py`, `test_deadline_normalizer.py`
   - Verification: SHA-256 whitespace-normalized content fingerprints prevent duplicate action generation. Relative and absolute dates normalize to ISO-8601 with `+05:30` offset.

10. **Dual-Database Support & Ephemeral PostgreSQL Testing**:
    - Location: `schoolbag/infrastructure/database.py` & `sqlite_store.py`
    - Test File: `test_transactional_concurrency.py`
    - Verification: Runs workflow slice and concurrent optimistic locking against an ephemeral PostgreSQL 16 cluster launched dynamically on loopback.
