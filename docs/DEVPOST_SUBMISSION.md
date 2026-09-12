# Devpost Submission Draft: Schoolbag

## Project Title
**Schoolbag: Human-Approved School Assistant for Busy Families**

## Elevator Pitch
Turn chaotic school WhatsApp forwards and circulars into clear family actions, calendar events, and parent-authorized decisions with strictly ₹0.00 personal spend.

---

## 1. Track
**Everyday Agents** (Agents for Humans Hackathon)

---

## 2. Inspiration

Every evening across India, millions of parents experience the same household stress: dozens of school WhatsApp group forwards, circular photos, fee reminders, costume requirements, and consent slips scattered across class groups.

For parents with multiple children—like Kavya in Class 5-B and Arun in Class 8-A—this communication explosion creates real anxiety:
- A field trip consent slip is buried under 40 "Thank you teacher" messages.
- An annual day costume fee of ₹350 is due Friday, but forgotten until the morning of.
- Both children have separate obligations on the exact same afternoon.

Existing calendar apps require manual data entry. But giving autonomous AI agents authority to pay school fees or autosign legal excursion waivers is unacceptable. Families need an assistant that eliminates clerical chaos while keeping parents firmly in the driver's seat.

---

## 3. What It Does

Schoolbag is an everyday AI assistant built specifically for school-going families:

1. **Intake & Structured Extraction**: Ingests messy school WhatsApp messages and circulars, automatically extracting concrete actions categorized by type:
   - 💳 **Fee Payments**: Amounts accurately parsed in Indian Rupees (₹ INR).
   - 📝 **Consent Slips**: Excursions, sports events, and medical declarations.
   - 📦 **Materials to Bring**: Chart papers, clay models, sports uniforms.
   - 🎓 **Exam Schedules**: Unit tests and revision requirements.
2. **IST Deadline Normalization**: Converts colloquial dates like "Friday 5 PM", "tomorrow morning", or "20th September" into precise ISO-8601 timestamps with Indian Standard Time (`+05:30`) offsets.
3. **Strands AI Advisory Loop**: When parents request deeper synthesis, Schoolbag invokes a two-stage agent advisory loop powered by the Strands framework and open-source models (`openai/gpt-oss-20b`). The agent is grounded against a single read-only bounded tool (`get_school_notice_context`) with zero write capabilities.
4. **The Human Authority Gate**: AI suggestions for fees and consent are strictly advisory. Any attempt by an autonomous bot or assistant to authorize payment or sign consent is immediately blocked by our backend with **HTTP 403 `HUMAN_APPROVAL_REQUIRED`**. Only a verified human parent can sign and authorize.
5. **Everyday Interoperability**:
   - **RFC 5545 iCalendar (.ics) Export**: One-click download of calendar events with UTC converted timestamps and a `-2h` alarm reminder (`VALARM`) compatible with Google Calendar, Apple Calendar, and Outlook.
   - **1-Click WhatsApp Family Draft**: Copies a clean, formatted reminder message to the clipboard for instant forwarding to family group chats.
6. **Family Weekly Board (Visual School Diary)**: A dedicated dashboard view inspired by the traditional Indian student diary:
   - Groups obligations side-by-side by child (`Kavya - Class 5-B` and `Arun - Class 8-A`).
   - Computes total pending fee liability across all children.
   - **Family Deadline Overlap Detection**: Warns parents when multiple children have concurrent obligations on the same day.

---

## 4. How We Built It

- **Backend**: Python 3.11+ with FastAPI, Pydantic v2 schemas (`extra="forbid"` for strict security), and transactional optimistic locking (`version` counters).
- **Dual-Engine Storage**: Thread-safe SQLite with Write-Ahead Logging (WAL) for local execution, plus zero-configuration ephemeral PostgreSQL 16 support for production verification.
- **Agent Architecture**: Strands Agents framework (`strands-agents[openai]==1.54.0` pattern) with Groq free-tier model adapter (`openai/gpt-oss-20b`) and offline deterministic fallback.
- **Inference Admission Safety**: Custom `InferenceAdmissionStore` featuring:
  - Single-active atomic concurrency lock (HTTP 429 `ASSISTANT_BUSY`).
  - Multi-tier sliding rate limiters (6 req/60s, 120 req/24h).
  - 15-minute provider 429 backoff cooldown.
  - Zero-send idempotent response caching.
- **Privacy & Pre-Inference Scrubber**: Automated regex redaction pipeline that strips phone numbers, emails, student IDs, Aadhaar numbers, and dates of birth before data ever touches the model.
- **Frontend**: React 18, TypeScript, Vite, and Lucide icons, styled with a high-contrast accessible design system.
- **Deployment Packaging**: Self-contained multi-stage `Dockerfile`, Render Free Docker manifest (`render.yaml`), and Vercel Hobby manifest (`vercel.json`).

---

## 5. Zero Personal Spend Guarantee

Throughout the design, implementation, and verification of Schoolbag, personal spend was maintained at strictly **₹0.00 / $0.00**:
- No paid cloud AI APIs were purchased or consumed.
- Offline mock transports and free-tier Groq endpoints power all model interactions.
- All test suites run locally without external network dependencies.

---

## 6. Challenges We Ran Into

1. **FastAPI Route Collisions**: Declaring literal routes like `/calendar.ics` alongside parameterized routes like `/{action_id}` required careful router sequence ordering so literal paths take precedence.
2. **Timezone Compatibility in RFC 5545**: Converting Indian Standard Time (+05:30) into universal UTC `Z` format while retaining calendar-level `X-WR-TIMEZONE:Asia/Kolkata` ensured alarms fire accurately across Android, iOS, and desktop calendar clients.
3. **Strict Pydantic Validation in Canary Tests**: Using `extra="forbid"` in Pydantic models caught unvetted test payload keys early, ensuring rigid schema enforcement across the API boundary.

---

## 7. Accomplishments That We're Proud Of

- **100% Green Test Suite**:
  - **37/37 Backend Pytest Tests** (including RFC 5545 calendar formatting, Strands advisory loop, ephemeral PostgreSQL concurrency, and security headers).
  - **10/10 Frontend Vitest Tests** (including calendar export, WhatsApp clipboard draft, and Family Weekly Board).
  - **22/22 End-to-End Release Smoke Stages**.
  - **11/11 Live Canary Verification Stages**.
- **The Human Authority Gate**: Demonstrating that AI assistants can be deeply useful without taking over human parental authority.
- **Cultural Grounding**: Tailoring the solution to real everyday Indian school communication patterns (Kovai Vidya Mandir, Coimbatore presets, WhatsApp forwards, fees in ₹ INR).

---

## 8. What We Learned

AI in family software should operate like an attentive executive assistant, not an autonomous proxy. Parents don't want agents to make financial or legal decisions on their behalf; they want agents to organize the chaos, highlight conflicts, and present clear decision points for a human thumbs-up.

---

## 9. What's Next for Schoolbag

- **Tamil & Multi-Language Support**: Processing school notices in Tamil, Hindi, and regional languages.
- **Direct School Calendar Subscriptions**: Serving a persistent `.ics` calendar URL that parents can subscribe to in Google Calendar for automatic live synchronization.
- **SMS & Low-Bandwidth Fallback**: SMS reminder dispatch for families with limited smartphone connectivity.
