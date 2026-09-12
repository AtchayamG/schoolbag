# Schoolbag Review Queue

## Review Items for Evaluator (SB-001 through SB-005)

1. **Live Canary Evaluator (SB-005)**:
   - Location: `03_SCHOOLBAG/scripts/live_canary.py`
   - Command: `.\services\school_service\.venv\Scripts\python.exe scripts\live_canary.py`
   - Verification: Runs 11 end-to-end stages covering health, cookies, presets, intake, Strands AI advisory loop, HTTP 403 human gate enforcement, parent approval, single action `.ics` export, family calendar feed, and action completion.

2. **Demo Video Script & Devpost Submission (SB-005)**:
   - Locations: `docs/DEMO_VIDEO_SCRIPT.md` & `docs/DEVPOST_SUBMISSION.md`
   - Verification: 180-second timed production script with scene-by-scene timing, voiceover, and lower-thirds; comprehensive Everyday Agents track hackathon submission copy.

3. **RFC 5545 iCalendar Export & WhatsApp Family Coordination (SB-004)**:
   - Location: `services/school_service/src/schoolbag/infrastructure/calendar.py` & `apps/web/src/components/ActionCard.tsx`
   - Test File: `services/school_service/tests/test_calendar_export.py` & `apps/web/src/test/Workflow.test.tsx`
   - Verification: In the web workbench, click "Export .ics" on any action card to download a standard iCalendar event with UTC timestamp conversion and a `-2h` alarm trigger. Click "WhatsApp Draft" to copy a structured reminder to clipboard with confirmation toast.

4. **Multi-Child Family Weekly Board & Overlap Detection (SB-004)**:
   - Location: `apps/web/src/components/FamilyWeeklyBoard.tsx` & `apps/web/src/App.tsx`
   - Test File: `apps/web/src/test/Workflow.test.tsx` (tests 9 & 10)
   - Verification: Switch to the "Family Weekly Board (Visual Diary)" tab. Observe side-by-side columns for `Kavya - Class 5-B` and `Arun - Class 8-A`. The board aggregates total pending fee liabilities in ₹ INR and displays a warning banner if both children have concurrent deadlines on the same date. Click "Export Family Calendar (.ics)" for the consolidated family schedule feed.

5. **Strands Agent Advisory Loop & Bounded Read Tool (SB-003)**:
   - Location: `services/school_service/src/schoolbag/infrastructure/strands_agent.py` & `apps/web/src/components/NoticeCard.tsx`
   - Test File: `services/school_service/tests/test_strands_advisory.py`
   - Verification: In the web workbench, click "Analyze with Strands AI" on any notice card. Strands Agent invokes `get_school_notice_context` to inspect the notice, performs extraction, forces human approval on fee/consent items, and surfaces draft suggestions with truthful model provenance (`openai/gpt-oss-20b`).

6. **Atomic Inference Admission Control (SB-003)**:
   - Location: `services/school_service/src/schoolbag/infrastructure/admission.py`
   - Test File: `services/school_service/tests/test_strands_advisory.py`
   - Verification: Single-active atomic lock prevents concurrent inferences (HTTP 429), sliding window limits requests to 6/60s and 120/24h, 15-minute cooldown on 429 provider backoff, and idempotent replay avoids duplicate LLM calls.

7. **PII Pre-Inference Scrubbing (SB-003)**:
   - Location: `services/school_service/src/schoolbag/infrastructure/redaction.py`
   - Test File: `services/school_service/tests/test_strands_advisory.py`
   - Verification: Phone numbers, emails, student registration IDs, Aadhaar numbers, and DOB are redacted before dispatch to the model, preserving only minimal child alias (`Kavya`, `Arun`).

8. **Human Authority Gate Demonstration (SB-001)**:
   - Location: `apps/web/src/components/ActionCard.tsx`
   - Test File: `services/school_service/tests/test_human_approval.py`
   - Verification: In the web workbench, click "Simulate Assistant Approval (Expect 403)". The app sends `actor_type: "assistant"` to `/api/actions/{id}/approve`, which raises `HumanApprovalRequiredError` and returns HTTP 403 `HUMAN_APPROVAL_REQUIRED`.

9. **Security Headers & Production Origin Enforcement (SB-002)**:
   - Location: `services/school_service/src/schoolbag/interfaces/http/app.py` (`SecurityMiddleware`) & `session.py` (`validate_production_request`)
   - Test File: `services/school_service/tests/test_config_and_security.py`
   - Verification: Responses enforce `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`. In production, unlisted external origins on mutation requests receive HTTP 403 `ORIGIN_REFUSED`.

10. **Zero-Spend Cloud Deployment Packaging (SB-002)**:
    - Manifests: `03_SCHOOLBAG/render.yaml` (Render Free Docker web service with `/api/health`) and `03_SCHOOLBAG/vercel.json` (Vercel Hobby static web + reverse proxy).
    - Verification: Both configs use ₹0.00 / $0.00 spend and zero credentials.

11. **Expanded Tamil Nadu Presets (SB-002)**:
    - Location: `services/school_service/src/schoolbag/infrastructure/seed_data.py`
    - Scenarios: 4 scenarios (Annual Day, Science Fair, Board Exams, Sports Day at Nehru Stadium, Coimbatore).

12. **Dual-Database Support & Ephemeral PostgreSQL Testing**:
    - Location: `schoolbag/infrastructure/database.py` & `sqlite_store.py`
    - Test File: `test_transactional_concurrency.py`
    - Verification: Runs workflow slice and concurrent optimistic locking against an ephemeral PostgreSQL 16 cluster launched dynamically on loopback.
