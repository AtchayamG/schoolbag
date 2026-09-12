# Schoolbag Demo Video Script & Production Guide

- **Product**: Schoolbag (Project 3)
- **Track**: Everyday Agents (Agents for Humans Hackathon)
- **Duration**: 180 Seconds (3 Minutes)
- **Resolution**: 1920x1080 (1080p, 60fps)
- **Voiceover**: Clear, engaging, professional Indian English neural voice (e.g. en-IN-PrabhatNeural or en-IN-NeerjaNeural)
- **Spend**: ₹0.00 / $0.00

---

## 1. Timing Breakdown & Storyboard

| Timestamp | Scene / Visual Action | Voiceover Narration | Lower-Third Caption |
| :--- | :--- | :--- | :--- |
| **0:00 - 0:18** | **Title Card & Problem**: Screen shows typical chaotic school WhatsApp group with multiple forwards, circular photos, fee reminders, and consent forms. | "Every school evening in India, parents face the same chaos: dozens of WhatsApp forwards, circular photos, and last-minute reminders from school groups. With multiple children in different classes, fees get missed, consent slips get forgotten, and parents scramble." | **Schoolbag: The Human-Approved Family School Assistant**<br>*Problem: Chaotic School WhatsApp Forwards & Circulars* |
| **0:18 - 0:42** | **App Header & Synthetic Presets**: Browser navigates to Schoolbag. Show the Evaluator Guide banner, ₹0.00 spend badge, and minimal identifier guarantee. Click "Ingest School Notice" and select "Annual Day Field Trip & Costume Fee" for Kovai Vidya Mandir, Coimbatore. | "Meet Schoolbag. Built specifically for Indian families, Schoolbag turns chaotic school communications into clear, actionable family obligations. We respect privacy: only minimal aliases like Kavya and Arun are used—never DOBs, Aadhaar, or medical records." | **Zero Personal Spend (₹0.00 / $0.00)**<br>*Minimal Identifiers: Child Alias Only (Kavya & Arun)* |
| **0:42 - 1:08** | **Rule Extraction & IST Normalization**: The notice appears in the feed. Show the extracted actions: ₹350 Costume Fee, Field Trip Consent Slip, and Science Fair materials. Show deadline normalized to Friday 5:00 PM IST (+05:30). | "Instantly, Schoolbag parses the notice into structured actions: a 350-rupee costume fee, an excursion consent form, and chart paper materials. Deadlines are automatically normalized to Indian Standard Time with exact date and time parsing." | **Rule-Based Extraction & IST Normalizer**<br>*₹350 Fee • Consent Slip • Materials Due Friday 5 PM IST* |
| **1:08 - 1:35** | **Strands AI Advisory Loop**: Click "Analyze with Strands AI" on the notice card. The spinner runs, bounded tool `get_school_notice_context` executes, and the Strands Advisory card renders with `openai/gpt-oss-20b` attribution and Urgent Priority badge. | "When parents want deeper synthesis, they click 'Analyze with Strands AI'. Powered by the Strands agent framework and open-source models, the agent executes a single bounded read tool to inspect the circular. Notice our strict safety guardrail: all fee and consent suggestions are forced to require human parental approval." | **Strands Agent Advisory Loop**<br>*Bounded Read Tool: get_school_notice_context • openai/gpt-oss-20b* |
| **1:35 - 2:00** | **The Human Authority Gate (HTTP 403)**: On the fee action card, click "Simulate Assistant Approval (Expect 403)". A prominent red rejection banner appears: `[HTTP 403 - HUMAN_APPROVAL_REQUIRED]`. Then click "Parent Sign & Authorize" and see it turn green with parent audit timestamp. | "Here is our core domain invariant: autonomous agents must never spend family money or autosign school consent. If an assistant attempts to approve this fee, our backend rejects it with HTTP 403 Human Approval Required. Only a verified human parent can authorize payment and sign consent." | **Domain Safety: Human Authority Gate**<br>*HTTP 403 HUMAN_APPROVAL_REQUIRED on Bot Approval Attempt* |
| **2:00 - 2:25** | **Interoperability (.ics Export & WhatsApp Draft)**: Click "Export .ics" on the action card to download the calendar event. Click "WhatsApp Draft" and show the visual feedback toast "Copied Draft!" with formatted family reminder. | "Schoolbag integrates seamlessly into everyday household routines. With one click, export an RFC 5545 iCalendar event with a 2-hour pre-deadline alarm to Google Calendar or Apple Calendar. Or click 'WhatsApp Draft' to copy a pre-formatted message to coordinate with your spouse in seconds." | **Everyday Interoperability**<br>*RFC 5545 iCalendar (.ics) with -2h Alarm • 1-Click WhatsApp Draft* |
| **2:25 - 2:48** | **Family Weekly Board (Visual Diary)**: Click the "Family Weekly Board (Visual Diary)" tab. Show side-by-side columns for Kavya (Class 5-B) and Arun (Class 8-A). Show total pending fees (₹550 INR) and the yellow "Family Deadline Overlap Detected" banner. | "For multi-child households, switch to the Family Weekly Board—designed around the familiar Indian school diary metaphor. It tracks Kavya in Class 5-B and Arun in Class 8-A side-by-side, sums pending fee liabilities, and alerts parents when multiple children have overlapping deadlines on the same day." | **Family Weekly Board (Visual School Diary)**<br>*Multi-Child Side-by-Side • Overlap Detection • Pending Fees* |
| **2:48 - 3:00** | **Architecture & Provenance Card**: Scroll to the footer provenance card disclosing the engine, rate limits, SQLite WAL / Postgres dual support, and zero spend declaration. | "Schoolbag operates at strictly zero personal spend using free-tier and offline architectures, runs on SQLite or PostgreSQL, and puts parents firmly in control. Schoolbag: empowering families, one school circular at a time. Thank you." | **Schoolbag: Everyday AI Family Assistant**<br>*₹0.00 Spend • 100% Parent Authority • Open Source* |

---

## 2. Production Audio & Visual Cues

### Audio Design:
- **Background Music**: Low-volume, subtle, uplifting acoustic/corporate tech track (ducked to -22dB during speech).
- **Voiceover**: Clean, noise-free narration with 0.5s pauses between scene transitions.
- **Sound Effects (Subtle)**:
  - *Swoosh*: Tab transitions between Feed and Weekly Board.
  - *Chime*: When "Parent Sign & Authorize" turns green.
  - *Click*: When "WhatsApp Draft" displays "Copied Draft!".

### Visual Polish:
- **Cursor**: Smooth highlighted cursor with yellow halo click animations.
- **Zooms**: Subtle 1.1x digital zoom into the red HTTP 403 error banner and the Strands attribution badge.
- **Lower-Thirds**: Elegant rounded slate-dark pill cards with teal accents at the bottom center.
