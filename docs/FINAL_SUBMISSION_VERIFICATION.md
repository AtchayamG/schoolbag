# Final submission verification

Authenticated Devpost API readback on 2026-09-14 confirms submission to Agents for Humans.

- Public page: https://devpost.com/software/schoolbag-human-approved-school-assistant
- Submitted at: 2026-09-14T01:07:22.757-04:00
- Video: https://youtu.be/xxQ9WQwkDlk
- Status: submitted (non-null hackathon submitted_at).
- The API supplies the timestamp even though the participant browser UI does not.
- Corrected architecture PNG and PDF are included in this release commit.
- No application code was changed in this reconciliation.

## Submitted description

Inspiration

School notices arrive as scattered messages: a fee deadline, materials for class, a consent slip and an exam reminder. For families with more than one child, the hard part is keeping those obligations together.

What it does

Schoolbag turns pasted notice text into a reviewable family action list. It associates notices with child aliases, normalizes supported deadline expressions, organizes actions in a family board, and exports calendar events. Parents can copy reminder drafts for sharing themselves.

An explicit Strands advisory action uses the notice and extracted actions as bounded read-only context. Parents review suggestions and record approval or completion themselves. The application does not pay fees, sign school forms or send WhatsApp messages.

How we built it

The React/TypeScript interface calls FastAPI on Vercel. Neon PostgreSQL stores notices, actions, versions and audit events; SQLite supports local use. Notice intake and deadline processing are distinct from the Strands advisory endpoint. Strands uses a Groq model adapter, a bounded context tool, pre-inference redaction, admission limits and provenance checks.

Calendar export uses iCalendar files with timezone-aware timestamps and reminders. The weekly board groups actions by child and helps expose overlapping deadlines.

Why it matters

The intended outcome is one clear list of what the family needs to review and do, while consequential decisions remain with the parent. Schoolbag enters Everyday Agents.

Challenges and lessons

We corrected differences between frontend expectations and persisted API fields, session-start ordering and displayed audit timestamps. The lesson was to verify the full hosted workflow, not just isolated components.

Try it

Open https://schoolbag-afh.vercel.app, start a family workspace and use the synthetic notice presets. Review the resulting actions, request Strands advice, approve an action through the parent control, download its calendar file and inspect the family board.

Source and setup: https://github.com/AtchayamG/schoolbag

Current limits

The public demo uses synthetic child aliases and parent roles; it does not verify real-world parental identity. Paste notice text: direct WhatsApp, email and PDF/OCR ingestion are not claimed. Redaction is a best-effort pattern filter, not a guarantee that arbitrary personal information will be removed. Free-tier limits may temporarily restrict inference. No AgentCore deployment is claimed.

Next

Test with families, improve regional-language notice handling, and introduce real household identity and access controls before personal-data use.
