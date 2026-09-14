# Schoolbag Handover & Evaluator Quickstart Guide

## Project Summary
- **Task ID**: `SB-005` (Final Production Packaging & Submission)
- **Product**: Schoolbag (Project 3)
- **Track**: Everyday Agents (Agents for Humans Hackathon)
- **Worktree / Directory**: `03_SCHOOLBAG/`
- **Active Branch**: `worker/agy/SB-005`
- **Total Spend**: **₹0.00 / $0.00** (Zero external paid APIs, deterministic synthetic engine + Groq free tier / offline mock transport)
- **Zero Secrets**: No API keys or credentials stored in repository

---

## 1. Quick Verification Commands

### Run Full 22-Stage Release Smoke Suite
```bash
cd services/school_service
.\.venv\Scripts\python.exe ..\..\scripts\release_smoke.py
```
*Expected Output*: `ALL 22/22 STAGES PASSED SUCCESSFULLY!`

### Run 11-Stage Live Canary Suite
```bash
cd 03_SCHOOLBAG
.\services\school_service\.venv\Scripts\python.exe scripts\live_canary.py
```
*Expected Output*: `ALL 11 CANARY STAGES PASSED SUCCESSFULLY!`

### Run Backend Pytest Suite (37 Tests)
```bash
cd services/school_service
.\.venv\Scripts\python.exe -m pytest -v
```
*Expected Output*: `37 passed in ~16.5s` (including 3 RFC 5545 calendar tests, 12 Strands agent tests, ephemeral PostgreSQL 16, and production security tests).

### Run Frontend Vitest Suite (10 Tests)
```bash
cd apps/web
cmd.exe /c npm test -- --run
```
*Expected Output*: `10 passed (1 file)`.

### Verify Web Build & Linting
```bash
cd apps/web
cmd.exe /c npm run lint
cmd.exe /c npm run build
```
*Expected Output*: ESLint 0 warnings, Vite production build completed to `apps/web/dist/`.

### Run Python Quality Checks
```bash
cd 03_SCHOOLBAG
.\services\school_service\.venv\Scripts\ruff.exe check services/school_service/src services/school_service/tests scripts
.\services\school_service\.venv\Scripts\ruff.exe format --check services/school_service/src services/school_service/tests scripts
```
*Expected Output*: All passed with 0 errors across all 37 source files.

---

## 2. Interactive Browser Review

To launch the fullstack application in browser review mode:
```bash
cd 03_SCHOOLBAG
.\services\school_service\.venv\Scripts\python.exe scripts\browser_review_server.py --port 8000
```
Then navigate to `http://localhost:8000` to review:
1. **Notice Feed**: Ingest synthetic school WhatsApp forwards for Kovai Vidya Mandir, Coimbatore.
2. **Strands AI Advisory**: Click **"Analyze with Strands AI"** on any notice to trigger the bounded tool advisory loop.
3. **Mandatory Human Gate**: Try clicking "Simulate Assistant Approval (Expect 403)" to verify non-parent approval blocking.
4. **Parent Approval**: Click "Parent Sign & Authorize" to simulate human parent authorization.
5. **iCalendar (.ics) Export**: Click "Export .ics" on any action to download an RFC 5545 calendar event with a 2-hour pre-deadline alarm reminder.
6. **WhatsApp Family Draft**: Click "WhatsApp Draft" to copy an instant formatted family reminder to your clipboard.
7. **Family Weekly Board**: Click "Family Weekly Board (Visual Diary)" tab to view the multi-child side-by-side view (Kavya & Arun), aggregate pending fee totals, family deadline overlap detection, and consolidated `.ics` family calendar feed.
8. **Truthful Disclosures**: Inspect the footer provenance card disclosing the rule engine, Strands agent seam, and zero-spend declarations.

---

## 3. Submission Documentation
- **Demo Video Script**: `docs/DEMO_VIDEO_SCRIPT.md` (180-second timed production script with captions and cues).
- **Devpost Submission**: `docs/DEVPOST_SUBMISSION.md` (Everyday Agents track submission copy).
- **Milestone Acceptance Records**: `docs/SB-001_ACCEPTANCE.md` through `docs/SB-005_ACCEPTANCE.md`.
-
## Claude Final Submission Handoff (2026-09-14)
- Devpost draft `1181709`, slug `schoolbag-human-approved-school-assistant`; track **Everyday Agents**; Individual; India.
- Repo https://github.com/AtchayamG/schoolbag | live https://schoolbag-afh.vercel.app | video https://youtu.be/xxQ9WQwkDlk
- Architecture: `architecture/schoolbag_architecture_readable.png` (or PDF only if explicitly required). Thumbnail is already uploaded; do not repeat.
- AWS Builder ID: `atchayamganesh@gmail.com`. Testing: start family workspace, use synthetic presets, review actions, request Strands advice, approve, download calendar, inspect board.
- Truth limits: synthetic aliases/roles, paste text only, no direct WhatsApp/email/PDF/OCR ingestion, payment/signing/automatic messaging, or AgentCore claim. Submit only after authenticated Devpost readback shows Submitted and timestamp.

---

## Devpost submission completed and verified (2026-09-14)

TASK: Final Devpost submission
WORKER: Claude, senior release and Devpost submission engineer
STATUS: COMPLETED — verified by authenticated Devpost readback

**Result:** Schoolbag is **Submitted** to the Agents for Humans Hackathon.
Submission ID `1181709`, track **Everyday Agents**, public project page
https://devpost.com/software/schoolbag-human-approved-school-assistant

Verified from the authenticated page
`/submit-to/30317-agents-for-humans-hackathon/manage/submissions`, which shows the
literal `SUBMITTED` badge; the project page shows `SUBMITTED TO — Agents for
Humans Hackathon`; the wizard reads 4/5 steps done with Manage team, Project
overview, Project details and Additional info all complete.

**No `submitted_at` is claimed.** Devpost exposes no per-submission submitted_at
in its participant UI — only the deadline and a project "updated" date. Observed
submission time from the session was ~2026-09-14T10:20–10:38+05:30.

**Fields saved:** Submitter Type `Individual`; Country `India`; Track
`Everyday Agents`; repo `https://github.com/AtchayamG/schoolbag`; AWS Builder ID
`atchayamganesh@gmail.com`; live demo `https://schoolbag-afh.vercel.app`;
1122-character testing instructions; video `https://youtu.be/xxQ9WQwkDlk`
(re-entered on the Project details step, where the field rendered empty and would
otherwise have been cleared on save). Organization name and bonus blog URL left
blank deliberately.

**Architecture diagram:** the required upload was empty (`File can't be blank`).
Uploaded the local working-tree `architecture/schoolbag_architecture_readable.png`
(310,972 bytes) and also added it to the public image gallery with a caption.

KNOWN_ISSUE / ACTION FOR OWNER: the repo copy of that diagram is **stale** —
`architecture/schoolbag_architecture_readable.png` and
`architecture/schoolbag_architecture.pdf` are both modified-and-uncommitted
locally. The submitted diagram is the correct newer one, but **the public repo
still shows the old diagram** until these files are committed and pushed. That
push was not performed here (public repository change, not authorised in this task).

TRUTH BOUNDARIES: the submitted testing instructions state explicitly that school
notices are **pasted or typed in**, that Schoolbag does not connect to WhatsApp,
email, PDFs or OCR and reads no inbox, and that the WhatsApp family draft is
copied to the parent's clipboard for them to send — nothing is sent, paid, signed
or ordered automatically. Approval is refused for non-parent actors with HTTP 403
`HUMAN_APPROVAL_REQUIRED`. No AgentCore deployment and no verified real-world
parent, child or school identities are claimed; all presets are synthetic.

A wording caveat was added to `docs/DEVPOST_SUBMISSION.md`: its section 3 phrase
"Ingests messy school WhatsApp messages" is shorthand for pasted content and
should not be reused as-is in public copy without the paste-only qualifier.

SPEND: ₹0.00 / $0.00.

NEXT_SAFE_ACTION: optionally commit and push the updated `architecture/` files so
the public repo matches the submitted diagram. Editing is allowed until the
deadline (Sep 15, 2026 @ 5:30am GMT+5:30); after it, do not edit anything.
