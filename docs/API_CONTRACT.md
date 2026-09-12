# Schoolbag API Contract & Endpoint Reference

Base URL: `/api`

All endpoints return JSON responses. Unknown `/api/*` endpoints strictly return HTTP 404 with standard error format:
```json
{
  "error": "NOT_FOUND",
  "message": "API endpoint '/api/xyz' does not exist.",
  "details": {}
}
```

---

## 1. Workspaces & Session

### `POST /api/workspaces`
Initializes or refreshes a workspace session. Sets an `HttpOnly`, `SameSite=Lax` session cookie (`schoolbag_session`).
- **Request Body**:
  ```json
  { "name": "Kovai Family Workspace" }
  ```
- **Response** (200 / 201):
  ```json
  {
    "workspace_id": "ws_1a2b3c4d5e6f...",
    "session_token": "sec_...",
    "notice_count": 0,
    "capacity_limit": 50,
    "created_at": "2026-09-14T08:00:00+05:30"
  }
  ```

### `GET /api/workspaces/current`
Returns current session workspace metadata.
- **Response** (200): `WorkspaceResponse`

---

## 2. Notices

### `POST /api/notices`
Ingests school communication, extracts actionable items, computes deduplication fingerprints, and saves the aggregate.
- **Headers**:
  - `Idempotency-Key` (optional string)
- **Request Body**:
  ```json
  {
    "source_type": "whatsapp",
    "class_name": "Class 5-B",
    "child_alias": "Kavya",
    "title": "Annual Day Costume Fee & Field Trip",
    "raw_body": "Please pay Rs 350 costume fee by Friday 5 PM...",
    "raw_due_text": "Friday 5 PM",
    "idempotency_key": "optional_key"
  }
  ```
- **Response** (201 Created or 200 OK for Duplicate Replay):
  ```json
  {
    "notice": {
      "notice_id": "not_1a2b3c...",
      "workspace_id": "ws_...",
      "source_type": "whatsapp",
      "class_name": "Class 5-B",
      "child_alias": "Kavya",
      "title": "Annual Day Costume Fee & Field Trip",
      "raw_body": "...",
      "fingerprint": "sha256_hash...",
      "version": 1,
      "created_at": "2026-09-14T08:30:00+05:30"
    },
    "actions": [
      {
        "action_id": "act_fee_123...",
        "notice_id": "not_1a2b3c...",
        "action_type": "fee_payment",
        "category": "fees",
        "title": "Annual Day Costume Fee",
        "raw_description": "...",
        "amount_inr": 350.0,
        "raw_deadline": "Friday 5 PM",
        "normalized_deadline": "2026-09-18T17:00:00+05:30",
        "status": "draft_ready",
        "approval_required": true,
        "version": 1,
        "confidence": 0.95,
        "extraction_provenance": {
          "engine": "deterministic",
          "provider": "synthetic",
          "advisory_only": true
        }
      }
    ],
    "is_deduplicated": false
  }
  ```

### `GET /api/notices`
Lists ingested notices for current workspace.
- **Query Params**:
  - `child_alias` (optional)
  - `class_name` (optional)
  - `source_type` (optional)

### `GET /api/notices/{id}`
Returns complete notice aggregate including child actions, reminder drafts, and full audit history.

---

## 3. Actions & Human Authority Gate

### `GET /api/actions`
Lists actions for current workspace.
- **Query Params**: `notice_id`, `status`

### `PATCH /api/actions/{id}/deadline`
Updates deadline text, normalizes to IST datetime, bumps action version, and appends audit event.
- **Request Body**:
  ```json
  {
    "expected_version": 1,
    "raw_deadline": "Next Friday 5 PM",
    "actor_name": "Parent"
  }
  ```

### `POST /api/actions/{id}/approve`
Executes human authority check.
- **Request Body**:
  ```json
  {
    "expected_version": 1,
    "actor_type": "parent",
    "actor_name": "Parent",
    "notes": "Authorized via UPI payment receipt"
  }
  ```
- **Responses**:
  - **403 Forbidden** if `actor_type != "parent"`:
    ```json
    {
      "error": "HUMAN_APPROVAL_REQUIRED",
      "message": "Action 'act_...' requires explicit human parent approval.",
      "details": { "actor_type": "assistant", "action_type": "fee_payment" }
    }
    ```
  - **409 Conflict** if `expected_version` does not match current version (`STATE_CONFLICT`).
  - **200 OK** if approved: returns updated action with `status: "approved"`.

### `POST /api/actions/{id}/complete`
Transitions approved action to completed state.
- **Request Body**:
  ```json
  {
    "expected_version": 2,
    "actor_name": "Parent",
    "notes": "Paid Rs 350 to teacher"
  }
  ```

---

## 4. Reminders & Calendar Drafts

### `POST /api/actions/{id}/reminders`
Schedules an advisory reminder draft.
- **Request Body**:
  ```json
  {
    "expected_action_version": 1,
    "channel": "calendar",
    "scheduled_for": "2026-09-18T17:00:00+05:30",
    "message_body": "Pay Costume Fee ₹350",
    "actor_name": "Parent"
  }
  ```
- **Response** (201 Created):
  ```json
  {
    "reminder_id": "rem_...",
    "action_id": "act_...",
    "channel": "calendar",
    "scheduled_for": "2026-09-18T17:00:00+05:30",
    "is_draft": true,
    "is_dispatched": false,
    "created_at": "2026-09-14T08:35:00+05:30"
  }
  ```

---

## 5. System Probes & Presets

### `GET /api/health`
Returns system status, active database engine, extractor mode, and advisory disclosures.

### `GET /api/ready`
Returns HTTP 200 `{"status": "ready", "database": "connected"}` if the database answers queries.

### `GET /api/presets`
Returns believable synthetic scenarios for Kovai Vidya Mandir, Coimbatore (Annual Day, Field Trip, Science Exhibition, Exams).
