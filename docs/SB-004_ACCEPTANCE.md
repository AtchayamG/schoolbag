# SB-004 Acceptance: Calendar Export (.ics), WhatsApp Family Share & Multi-Child Board

- **Task ID**: `SB-004`
- **Worker**: AGY (Senior Full-Stack Developer)
- **Branch**: `worker/agy/SB-004`
- **Base**: `worker/agy/SB-003` (Commit `30d27ca`)
- **Status**: COMPLETE & VERIFIED
- **Total Personal Spend**: **₹0.00 / $0.00**
- **External Paid APIs**: **None (Zero paid cloud APIs; pure local RFC 5545 generator)**

---

## 1. Executive Summary

Milestone `SB-004` implements household calendar interoperability, family WhatsApp coordination, and the consolidated multi-child weekly schedule board for Project 3 (Schoolbag).
1. **RFC 5545 iCalendar (.ics) Export**: Generates compliant `.ics` calendar files with UTC converted timestamps (`Z` format), `X-WR-TIMEZONE:Asia/Kolkata`, and a `-2h` alarm reminder (`VALARM`) 2 hours prior to school deadlines. Works natively with Apple Calendar, Google Calendar, and Microsoft Outlook.
2. **Single Action & Aggregate Family Feed**:
   - Single Action: `GET /api/actions/{action_id}/calendar.ics` downloads an `.ics` event for that specific fee or consent deadline.
   - Aggregate Feed: `GET /api/actions/calendar.ics` downloads the consolidated calendar for all pending and approved family actions.
3. **WhatsApp Coordination Draft**: Single-click "WhatsApp Draft" button copies a structured, pre-formatted message to the parent's clipboard for instant sharing with spouses, grandparents, or family group chats.
4. **Family Weekly Board (Visual Diary Metaphor)**:
   - Dedicated dashboard view organizing obligations side-by-side by child (`Kavya - Class 5-B` and `Arun - Class 8-A`).
   - Computes total pending fee liability across all children in ₹ INR.
   - Automatic **Family Deadline Overlap Detection** alerting parents when multiple children have concurrent obligations on the same calendar day.
5. **Strict Safety Invariants Preserved**:
   - Zero personal spend maintained (₹0.00 / $0.00).
   - Minimal identifiers only (`Kavya`, `Arun`; no DOB, medical history, or student IDs).
   - Human authority gate unchanged (non-parent approval receives HTTP 403).

---

## 2. Implemented Architecture & Seams

### 2.1 RFC 5545 iCalendar Generator (`calendar.py`)
- **Location**: `services/school_service/src/schoolbag/infrastructure/calendar.py`
- **Functionality**:
  - `generate_action_ics(action, notice_context)`: Generates single VEVENT calendar string.
  - `generate_workspace_calendar_ics(actions, notices_by_id)`: Generates multi-event VCALENDAR feed.
  - Timezone handling: Converts IST (+05:30) deadline strings into universal UTC `Z` timestamps (`YYYYMMDDTHHMMSSZ`).
  - Alarm Trigger: Includes `BEGIN:VALARM` with `TRIGGER:-PT2H` for notifications 2 hours prior to deadline.
  - Safety & Provenance: Injects Kovai Vidya Mandir school context, action title, description, and status into summary and description fields.

### 2.2 HTTP Calendar Endpoints (`routes/actions.py`)
- **Location**: `services/school_service/src/schoolbag/interfaces/http/routes/actions.py`
- **Endpoints**:
  - `GET /api/actions/calendar.ics`: Returns aggregate family schedule with `Content-Type: text/calendar; charset=utf-8` and `Content-Disposition: attachment; filename=schoolbag_family_schedule.ics`.
  - `GET /api/actions/{action_id}/calendar.ics`: Returns single-action calendar event with `Content-Disposition: attachment; filename=schoolbag_action_{action_id}.ics`.
  - Route order: `/calendar.ics` is declared before `/{action_id}` to prevent FastAPI route collision.

### 2.3 Action Card Export & WhatsApp Share (`ActionCard.tsx`)
- **Location**: `apps/web/src/components/ActionCard.tsx`
- **UI Enhancements**:
  - **Export .ics Button**: Downloads RFC 5545 `.ics` file directly to the user's device.
  - **WhatsApp Draft Button**: Copies formatted WhatsApp reminder string (`📌 Schoolbag Reminder...`) with immediate visual feedback toast ("Copied Draft!").

### 2.4 Family Weekly Board Component (`FamilyWeeklyBoard.tsx`)
- **Location**: `apps/web/src/components/FamilyWeeklyBoard.tsx`
- **Capabilities**:
  - Visual diary layout grouping actions by child alias (`Kavya` and `Arun`).
  - Consolidated pending fee metric (`Pending Fees: ₹X INR`).
  - One-click full family `.ics` calendar export.
  - Overlap warning banner (`Family Deadline Overlap Detected: Kavya & Arun on YYYY-MM-DD`).

### 2.5 View Switcher (`App.tsx`)
- **Location**: `apps/web/src/App.tsx`
- **Functionality**:
  - Tab controls allowing instant switching between `Feed & Action View` (3-column intake/action/audit view) and `Family Weekly Board (Visual Diary)`.

---

## 3. Verification Matrix

| Verification Check | Target | Result | Evidence |
| :--- | :--- | :--- | :--- |
| **Backend Pytest Suite** | 37 tests across 9 suites | **37/37 PASS (100%)** | `pytest -v` (16.5s) |
| **Calendar Export Suite** | 3 dedicated RFC 5545 tests | **3/3 PASS (100%)** | `test_calendar_export.py` |
| **Frontend Vitest Suite** | 10 component & workflow tests | **10/10 PASS (100%)** | `npm test -- --run` (2.45s) |
| **22-Stage Release Smoke** | Complete pipeline + Stages 21 & 22 | **22/22 PASS (100%)** | `release_smoke.py` |
| **TypeScript Typecheck** | `tsc` compilation | **PASS (0 errors)** | Clean Vite build |
| **ESLint Frontend Suite** | `eslint . --max-warnings 0` | **PASS (0 warnings)** | Clean ESLint |
| **Python Code Quality** | `ruff check src tests` | **PASS (0 errors)** | Clean ruff check |
| **Python Formatting** | `ruff format --check src tests` | **PASS (0 diffs)** | 34 files formatted |

---

## 4. Invariant Checklist

- [x] Zero Personal Spend: ₹0.00 / $0.00 verified.
- [x] Human Authority Gate: Preserved (non-parent approval returns HTTP 403).
- [x] Minimal Child Identifiers: Only `Kavya` and `Arun` used.
- [x] Zero changes to `01_BORROWED_STEPS`, `02_BENCHBOOK`, `00_PROGRAM_CONTROL`.
- [x] Calendar export compliant with RFC 5545.
- [x] All 22 release smoke stages green.
