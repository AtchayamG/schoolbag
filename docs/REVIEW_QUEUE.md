# Schoolbag Review Queue

## Review Items for Evaluator (SB-001 & SB-002)

1. **Human Authority Gate Demonstration**:
   - Location: `apps/web/src/components/ActionCard.tsx`
   - Test File: `services/school_service/tests/test_human_approval.py`
   - Verification: In the web workbench, click "Simulate Assistant Approval (Expect 403)". The app sends `actor_type: "assistant"` to `/api/actions/{id}/approve`, which raises `HumanApprovalRequiredError` and returns HTTP 403 `HUMAN_APPROVAL_REQUIRED`.

2. **Security Headers & Production Origin Enforcement (SB-002)**:
   - Location: `services/school_service/src/schoolbag/interfaces/http/app.py` (`SecurityMiddleware`) & `session.py` (`validate_production_request`)
   - Test File: `services/school_service/tests/test_config_and_security.py`
   - Verification: Responses enforce `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`. In production, unlisted external origins on mutation requests receive HTTP 403 `ORIGIN_REFUSED`.

3. **Zero-Spend Cloud Deployment Packaging (SB-002)**:
   - Manifests: `03_SCHOOLBAG/render.yaml` (Render Free Docker web service with `/api/health`) and `03_SCHOOLBAG/vercel.json` (Vercel Hobby static web + reverse proxy).
   - Verification: Both configs use ₹0.00 / $0.00 spend and zero credentials.

4. **Expanded Tamil Nadu Presets (SB-002)**:
   - Location: `services/school_service/src/schoolbag/infrastructure/seed_data.py`
   - Scenarios: Added 4th scenario (`preset-sports-day` - Annual Inter-School Athletics Meet at Nehru Stadium, Coimbatore, Class 8-A Arun, ₹200 fee, consent form).

5. **Evaluator Walkthrough Tour Banner (SB-002)**:
   - Location: `apps/web/src/components/Header.tsx`
   - Verification: Interactive "60-Second Evaluator Tour" collapsible guide, displaying version `v0.2.0` badge and live workspace capacity count.

6. **Deduplication Resilience & IST Deadline Normalization**:
   - Locations: `schoolbag/domain/workflow.py`, `schoolbag/infrastructure/normalizer.py`
   - Test Files: `test_deduplication.py`, `test_deadline_normalizer.py`
   - Verification: SHA-256 whitespace-normalized content fingerprints prevent duplicate action generation. Relative and absolute dates normalize to ISO-8601 with `+05:30` offset.

7. **Dual-Database Support & Ephemeral PostgreSQL Testing**:
   - Location: `schoolbag/infrastructure/database.py` & `sqlite_store.py`
   - Test File: `test_transactional_concurrency.py`
   - Verification: Runs workflow slice and concurrent optimistic locking against an ephemeral PostgreSQL 16 cluster launched dynamically on loopback.
