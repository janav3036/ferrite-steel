# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

# FERITE-STEEL — Claude Code Project Context

This file is the single source of truth for all Claude tools (Claude Code, Cowork,
Claude.ai) on every aspect of the FERITE-STEEL project. Read it fully before doing
anything. Never deviate from the decisions recorded here without explicit instruction
from Janav.

**Last updated:** 13 May 2026 (session 3)

---

## COWORK SESSION PROTOCOL

**At the start of every Cowork session:**
1. Read CLAUDE.md fully before doing anything
2. State which sections you've read and confirm current project state

**At the end of every Cowork session:**
1. Review everything discussed and decided in this session
2. Identify what has changed from what's in CLAUDE.md
3. Update only the affected sections to reflect current state
4. Update the "Last updated" date at the top
5. Write the changes back to CLAUDE.md
6. Confirm which sections were updated and what changed

Same rules as /md-write — rewrite sections, never append. Current state only.

---

## HOW THIS FILE WORKS

This file is maintained across sessions. At the end of every session, run `/md-write`
to update relevant sections with decisions made. At the start of every session, read
this file fully before taking any action.

**What gets updated:** Current state, models, architecture decisions, unresolved items,
client questions. Not a change log — sections are rewritten to reflect current reality,
not appended to.

---

## 0. Development Commands

All commands run from the project root (`ferite_steel/`). Activate the virtualenv first:

```bash
source .venv/bin/activate        # macOS/Linux
.venv\Scripts\activate           # Windows
```

```bash
# Run development server
python manage.py runserver

# Migrations — always review makemigrations output before migrating
python manage.py makemigrations
python manage.py migrate

# Run all tests
python manage.py test

# Run tests for a single app
python manage.py test aegis
python manage.py test quotations

# Create admin superuser
python manage.py createsuperuser

# Collect static files (needed before production deploy)
python manage.py collectstatic
```

**Together.ai SDK is not yet installed** — `quotations/services/llm.py` is a stub.
Install when implementing Phase 2: `pip install together` then pin in requirements.txt.

---

## 1. Project Overview

FERITE-STEEL is a Django-based CRM and business management system being built for
an iron and steel distribution company. It replaces manual quoting, gut-feel credit
decisions, unstructured lead management, and slow salesperson onboarding with an
automated, AI-assisted web system.

This is a paid client engagement managed solely by Janav, a second-year student
developer. The client CEO is taking a chance on Janav based on a personal connection.
Trust is being built incrementally through phased delivery. Every architectural
decision must be defensible to a non-technical client.

**Modules:**
1. Base Setup (complete)
2. Quotation Automator
3. Training System + Case Solver
4. Credit Risk AI
5. Lead Ranking + Inventory Intelligence
6. Internal AI Chatbot (confirmed add-on, fee TBD)
7. AI Voice Stand-in (proposed, NOT greenlit)

---

## 2. Developer Profile & Communication Rules

- Janav is the **sole developer**. There is no team.
- He is a second-year student with no prior real-world project experience.
- He prefers **granular, step-by-step explanations** — never skip steps or assume
  prior knowledge.
- When giving terminal/shell commands, always **specify which directory to run them
  in** and what the expected output is.
- When multiple approaches exist, **explain tradeoffs before recommending**.
- He prefers **direct, honest assessments** including unflattering ones — do not
  soften evaluations of his code, architecture, or positioning.
- **Working style preference:** Act as advisor/helper only. Guide Janav to figure
  things out himself first. Do not give direct answers unless he has tried and asked
  multiple times.

---

## 3. Current State

**Phase 1: Complete. Phase 2 UI largely complete — LLM integration and ingestion pending.**
**Current phase: Phase 2 — quotation UI/flow done; awaiting WhatsApp API approval and LLM wiring.**
**First deliverable: Quotation Automator (Module 2).**

### What is built
- Django project at `ferite_steel/` (macOS dev path: `/Users/janav/Programs/ferite_steel/`)
- PostgreSQL 16 database `ferite_steel_db` connected
- `CustomUser` model in `aegis` app with `team` field (`team_9`/`cs`/`market`/`corporate`) and role choices (`admin`/`lead`/`member`/`primary`/`rolling`/`loading_dock`)
- Full auth flow: login, logout, register (pending admin approval), password reset
- User management: add user, directory, edit role, approve, delete — all admin-gated; forms include team dropdown with **JavaScript role filter** (role options update dynamically based on selected team)
- `base.html` built — all templates extend it; nav gated by `request.user.role`
- Dashboard with lead/quotation stats, scoped by role (admin/lead see all; member sees own); + New Lead / + New Quotation / + Market Order buttons (Market Order button visible to market team + admin only)
- `quotations` app: `Customer`, `Lead`, `Quotation`, `QuotationLineItem`, `PricingEntry`, `Broker`, `MarketOrder` models
- Lead: company, industry, location, broker (optional FK) fields; list/create/detail views
- Quotation: full edit flow with inline formset (line items), JS auto-calculation (amount = rate × tons), WeasyPrint PDF
- Quotation versioning: Revise creates v2/v3 etc. cloned from current; all versions share a root's outcome
- Customer model: transport cost memory + `notes` field for AI context — upserted on every quotation save; pre-fills transport_extra on edit for returning customers
- Outcome (Win/Loss/Not Updated): shown on quotation detail as quick-select buttons; stored only on root quotation; shared across all versions
- Broker-sourced quotations: Send button hidden, "Internal Copy" badge shown; PDF header reads "INTERNAL — RATES ONLY"
- Send button: dummy (marks status='sent') — pending WhatsApp/email wiring
- Approve flow: lead and admin roles only
- LLM service at `quotations/services/llm.py` — `generate_quotation_draft(lead, entity_notes)` stub with full JSON output schema documented; raises `NotImplementedError` until wired; `quotation_create` calls it with graceful fallback to blank editor
- `lookup_pricing` tool definition at `quotations/services/tools/pricing.py`
- Broker model: name, company, phone, email, location, `notes` (AI context), is_active; list + create views at `/quotations/brokers/`; registered in admin
- MarketOrder model: full broker order flow — `new` → `rate_sent` → `broker_confirmed` → `do_pending` → `completed`; views + templates at `/quotations/market-orders/`
- Django admin themed with `django-jazzmin`; Customer, Broker, MarketOrder registered
- Static files served via `whitenoise`
- WeasyPrint installed (`pip install weasyprint` + `brew install pango` on macOS)

### What is NOT yet built (planned for next session)
- `Customer.handling_team` field — team assignment per customer; handover flow (lead/admin only)
- Customer list + detail views with team scope (`?scope=all` toggle for admin)
- `ProductKeyword` model — company-specific term mappings (e.g. "sariya" → "TMT Bars") injected into LLM system prompt
- `TeamEmailConfig` model — IMAP credentials per team for email ingestion
- Product catalog view at `/quotations/products/` + CSV upload view for bulk `PricingEntry` upsert
- `classify_message(text)` in `llm.py` — Step 1 LLM call; checks if a message is a product inquiry before creating a lead
- `generate_quotation_draft` full scaffold — system prompt with keyword injection, not-found item handling, together.ai TODO wiring
- `lookup_pricing` tool update — return `found: bool` alongside results
- `poll_emails` management command — IMAP polling with header pre-filter + classifier; demo uses a dummy Gmail account
- Email ingestion: dummy Gmail account for demo (to be deleted post-demo); WhatsApp ingestion deferred until Meta approval

### Pending before Phase 2 LLM logic can complete
- WhatsApp Business API Meta approval
- together.ai API key confirmed + together.ai client wired in `quotations/services/llm.py`
- Product Excel format reviewed (user to share file — see Section 10)
- Hosting decision confirmed (see Section 8)

---

## 4. Tech Stack

### Backend
- **Framework:** Django 6.0.3
- **Python:** 3.12
- **Database:** PostgreSQL 16, database name `ferite_steel_db`
- **ORM:** Django ORM only — no raw SQL unless unavoidable
- **Installed packages:** `psycopg2-binary` (PostgreSQL), `python-dotenv` (env vars),
  `whitenoise` (static files), `django-jazzmin` (admin theme),
  `djangorestframework` (installed, not yet used in views)

### Frontend
- **CSS Framework:** Bootstrap 5
- **Templating:** Django templates (Jinja2 is NOT used)
- **No frontend framework** (no React, Vue, etc.) — server-side rendered HTML only

### Server (On-Premise)
- **OS:** Windows Server 2016
- **CPU:** Intel Xeon Bronze 3106 (8-core, 1.7 GHz, no GPU)
- **RAM:** 32 GB
- **Storage:** 4 TB HDD

### Hosting (DECISION PENDING — see Section 8)
- **Option A:** Expose Windows Server directly via IIS + static IP
- **Option B (recommended):** Cloud VPS (Hetzner) + Gunicorn + Nginx. Django and
  PostgreSQL both on VPS. Windows Server retained for SAP/internal only.
- **Option C:** Cloudflare Tunnel in front of Windows Server
- **Decision blocker:** Client must confirm comfort with data leaving on-premise
  before Option B is finalised.

### AI / LLM
- **Provider:** together.ai (Janav has account access as of May 2026)
- **Why:** Server has no GPU; all AI workloads must be cloud API-based
- **Architecture split:**
  - Tool use / function calling → live-data modules (Quotation Automator,
    Credit Risk AI, Lead Ranking, Inventory Intelligence, Chatbot live queries)
  - RAG → static knowledge modules (Training + Case Solver, Chatbot knowledge base)
- **No MCP server** — Django-native tool use used instead
- **No local model hosting** of any kind

### Database Tools
- **Primary:** DataGrip 2025.1.3
- **Secondary:** pgAdmin 4 (retained)

---

## 5. Team & Employee Structure

### Overview
Client company has **4 teams**. Full breakdown confirmed by client in session 2.
Views and permissions differ based on both team and role.

### Team breakdown

| Team slug   | Display name   | Description                                                         | Roles                                  |
|-------------|----------------|---------------------------------------------------------------------|----------------------------------------|
| `team_9`    | Team 9         | Handles IndiaMART, JustDial, TradeIndia, BNL leads. One salesperson per platform. | `lead`, `member` |
| `cs`        | CS Team        | Customer Service. Clients handled jointly by the team.              | `lead`, `member`                       |
| `market`    | Market Team    | Broker-based orders. Two sub-teams: Primary and Rolling. Also has loading dock members. | `lead`, `primary`, `rolling`, `loading_dock` |
| `corporate` | Corporate Team | Details TBD; keeping as lead + member for now.                      | `lead`, `member`                       |

Admins have no team (`team = null`). The role dropdown in Add User / Edit Role forms
filters options via JavaScript based on the selected team.

### Market team workflow
Market team does not send formal quotations externally. Workflow:
1. Broker sends order → market member creates a Lead (with broker FK) and MarketOrder
2. Quotation editor used internally to calculate rates (PDF is "INTERNAL — RATES ONLY")
3. Rate sent back to broker → broker confirms → assigned to loading dock member → DO number issued

### Current implementation
`CustomUser` has:
- `team` — CharField choices: `team_9`, `cs`, `market`, `corporate` (nullable — admins have no team)
- `role` — CharField choices: `admin`, `lead`, `member`, `primary`, `rolling`, `loading_dock`

Role-based guards in views and templates use `request.user.role`. Team field is displayed
in the nav badge on `base.html`. Role filter JS is in `add_user.html` and `edit_user_role.html`.

---

## 6. Models

### CustomUser (aegis.models.CustomUser)
**Current fields:**
- `role` — CharField, choices: `admin`, `lead`, `member`, `primary`, `rolling`, `loading_dock`; default `member`
- `team` — CharField, choices: `team_9`, `cs`, `market`, `corporate`; nullable/blank (admins have no team)
- `phone` — CharField
- `branch` — CharField
- `employee_id` — IntegerField

### Customer (quotations.models.Customer)
Stores remembered transport costs per customer, matched by name + company (case-insensitive).
- `name`, `company`, `location`, `phone`, `email` — CharFields
- `transport_extra` — DecimalField (default 0)
- `loading_rate` — DecimalField (default 0.5 — ₹/ton)
- `notes` — TextField blank (AI context: discount preferences, special terms, etc.)
- `handling_team` — CharField choices: TEAM_CHOICES, nullable/blank (**planned — not yet built**; migration required)
- `updated_at` — auto_now DateTimeField
Auto-upserted whenever a quotation is saved.

### Broker (quotations.models.Broker)
Stores broker information for the Market team. Separate from Customer (different flow direction, no transport cost memory).
- `name`, `company`, `location`, `phone`, `email` — CharFields
- `notes` — TextField blank (AI context: usual margins, preferred products, etc.)
- `is_active` — BooleanField (default True)
- `created_at` — auto_now_add DateTimeField

### Lead (quotations.models.Lead)
- `customer_name`, `customer_phone`, `customer_email` — contact info
- `company`, `industry`, `location` — added in Phase 2
- `broker` — FK to Broker (nullable; set for market team leads)
- `raw_text` — raw enquiry text
- `notes`, `source`, `status`, `created_by`, `created_at`

### Quotation (quotations.models.Quotation)
- `quotation_number` — auto-generated: `QT-00001` or `QT-00001-v2` for revisions
- `lead` — FK to Lead
- `version` — IntegerField (default 1)
- `parent_quotation` — self-FK nullable (null = root version)
- `status` — choices: `draft`, `approved`, `sent`
- `outcome` — choices: `win`, `loss`, `not_updated`; stored only on root quotation
- `llm_raw_response` — TextField (stores raw JSON from LLM draft generation)
- `payment_terms`, `delivery_address` — CharFields
- `transport_extra`, `sgst_percent`, `cgst_percent` — DecimalFields
- `total_amount`, `notes`, `valid_until`
- `created_by`, `approved_by`, `created_at`, `approved_at`, `sent_at`

Broker-sourced quotations (where `lead.broker` is not null) are internal-only: Send button hidden, PDF header reads "INTERNAL — RATES ONLY".

### QuotationLineItem (quotations.models.QuotationLineItem)
- `quotation` — FK to Quotation
- `product_name`, `make` — CharFields
- `length` — DecimalField nullable
- `pcs` — IntegerField nullable
- `quantity` — DecimalField (tons)
- `unit_price`, `total_price` — DecimalFields
- `notes` — CharField

### MarketOrder (quotations.models.MarketOrder)
Tracks the Market team's broker order logistics flow, independent of the Quotation model.
- `broker` — FK to Broker (CASCADE)
- `quotation` — FK to Quotation (nullable; linked when internal rate quotation is generated)
- `sub_team` — CharField choices: `primary`, `rolling`
- `product_details` — TextField
- `quantity` — DecimalField (nullable)
- `status` — choices: `new`, `rate_sent`, `broker_confirmed`, `do_pending`, `completed`, `cancelled`
- `rate` — DecimalField (nullable; set when rate is sent to broker)
- `rate_sent_at`, `broker_confirmed_at`, `do_requested_at`, `do_issued_at` — DateTimeFields nullable
- `loading_dock_member` — FK to AUTH_USER_MODEL (nullable; assigned at broker_confirmed stage)
- `do_number` — CharField blank
- `notes` — TextField blank
- `created_by` — FK to AUTH_USER_MODEL
- `created_at` — auto_now_add DateTimeField

### ProductKeyword (quotations.models.ProductKeyword) — PLANNED
Maps company-specific client terms to canonical product names for LLM prompt injection.
- `keyword` — CharField (what clients say, e.g. "sariya", "angle", "12mm")
- `maps_to` — CharField (product name or code in PricingEntry, e.g. "TMT Bars 12mm")
- `notes` — CharField blank (e.g. "Hindi term for TMT bars")
- `is_active` — BooleanField (default True)
Admin-editable. Active keywords are fetched and injected into the LLM system prompt on every `generate_quotation_draft` call.

### TeamEmailConfig (quotations.models.TeamEmailConfig) — PLANNED
IMAP credentials for team shared email accounts, used by `poll_emails` management command.
- `team` — CharField choices: TEAM_CHOICES (unique per team)
- `email_address` — EmailField
- `imap_host`, `imap_username`, `imap_password` — CharFields
- `imap_port` — IntegerField (default 993)
- `use_ssl` — BooleanField (default True)
- `is_active` — BooleanField (default True)
Admin-only management (no user-facing view). Store password as env var reference in production.

### AUTH_USER_MODEL
`'aegis.CustomUser'` — set in settings.py

### Migration discipline
Never run `migrate` without first reviewing `makemigrations` output. Always inspect
migration files before applying.

---

## 7. Inventory & Stock Data

### Source
Client receives **three Excel files daily via WhatsApp**:
1. `Main_Stock.xlsx` — comprehensive stock: Angle, Channel, Beam, NPB, WPB, TMT,
   Red Material. Columns: SIZE, length, actual qty, received, sold, balance, rate.
   Sheet name = date (e.g. `01-04`). Multiple product categories laid out **horizontally**
   side by side on the same sheet.
2. `New_Plate_Stock.xlsx` — plate stock organised by physical plot/location
   (Plot No-557, 558, 560 etc.). Columns: Sizes, Pcs, Qty, In, Out, Open. Tracks
   steel grade (E250, E350), piece count, heat numbers, vehicle numbers.
3. `Stock_Rolling_New.xlsx` — rolling stock: Rolling Angle, Channel, Beam, Flat,
   TMT rods, Square sections. Columns: SIZE, QTY, IN, OUT, OPEN.

### Architecture decision
**Excel is transport only. PostgreSQL is the destination.**
- Excel arrives → Django parses it (openpyxl/pandas) → data upserted into PostgreSQL
  → file discarded
- All downstream modules (Lead Ranking, Inventory Intelligence) query the database,
  not the file
- Export feature to be built: users can download a fresh Excel generated from
  PostgreSQL on demand

### Pending questions (ask client)
- Who or what generates/maintains the daily Excel? Manual entry or auto-generated?
- Are all three files updated daily, or just some?
- Is the column layout and category structure identical every day, or does it vary?
- Does the file arrive as a fresh file each day, or as a new sheet added to the same file?

---

## 8. Hosting Decision

**Status: Unresolved. Must be confirmed before Phase 2 deployment planning.**

Three options discussed:

| Option | Description | Cost | Risk |
|--------|-------------|------|------|
| A | Expose Windows Server via IIS + static IP | Static IP from ISP (₹0–1,000/mo) + domain (₹800–1,200/yr) | Office internet = single point of failure. Security risk. |
| B (recommended) | Cloud VPS (Hetzner CX22: 2vCPU/4GB/40GB). Django + PostgreSQL on VPS. Windows Server for SAP only. Gunicorn + Nginx. | ~₹375–565/mo + domain | Best security, app independent of office internet |
| C | Cloudflare Tunnel in front of Windows Server. No port forwarding needed. | Domain only (₹800–1,200/yr) | Office internet = single point of failure |

**Decision blockers:**
- Client must confirm comfort with data living on a cloud server (not on-premise)
- Client must confirm whether their office has a static IP (affects Options A and C)

**Note:** If Option B is chosen, deployment changes from IIS + Waitress (Windows) to
Gunicorn + Nginx (Linux). The Non-Negotiables section must be updated accordingly.

---

## 9. ConvoGenie

**What it is:** convogenie.ai — a no-code AI chatbot/agent platform for businesses.
Incorporated April 2024, Bangalore (Convogenie Technologies Pvt Ltd). Handles generic
sales/support automation: lead engagement, FAQs, basic routing, sentiment analysis.

**Status:** Client has already paid for it. In a client meeting, Janav was compared
to ConvoGenie without knowing what it was. Client has asked whether FERITE-STEEL can
integrate with it. Janav told him he'd look into it.

**Current state:**
- Janav has access to the ConvoGenie account and has reviewed it
- Client had a meeting with ConvoGenie on 11 May 2026 — Janav gave him questions to ask
- If ConvoGenie uses technical language in the meeting, client will connect Janav
  directly to speak with their team
- Integration scope and API feasibility still TBD pending meeting outcome

**Key distinction:**
- ConvoGenie = generic no-code chatbot (FAQs, basic support, no business data access)
- FERITE-STEEL Module 6 = purpose-built chatbot with live SAP data, credit risk,
  pricing logic, inventory queries — entirely different capability

**Why Module 6 fee is not yet quoted:**
The chatbot tier and whether/how ConvoGenie integrates must be understood before
pricing Module 6. Do not quote a chatbot fee until this is resolved.

---

## 10. Client Questions (To Ask at Next Meeting)

These are outstanding questions that only the client can answer. Do not assume
resolved until explicitly confirmed.

### Product Pricing Excel
1. Share the product pricing Excel file so the CSV upload and `PricingEntry` model design can be validated against the actual column structure before building the upload view.

### Stock & Inventory
2. Who or what generates/maintains the daily Excel stock files — manual entry or
   auto-generated from somewhere?
3. Are all three Excel files (Main Stock, Plate Stock, Rolling Stock) updated daily,
   or just some of them?
4. Is the column layout and category structure in each file identical every day, or
   does it occasionally change?
5. Does the file arrive as a fresh file each day, or as a new sheet added to the
   same ongoing workbook?

### Corporate Team
6. What are the specific roles within the Corporate team? (Currently placeholder: lead + member.)

### Hosting
7. Is the client comfortable with business data living on a cloud server (not
   on-premise)? Required to confirm Option B.
8. Does the client's office have a static IP from their ISP? (Affects Options A and C.)

### ConvoGenie
9. What did ConvoGenie say in the meeting about API access and integration options?
10. What plan is the client on — does it include API access?
11. What does the client actually want the two systems to do together?

### WhatsApp Business API
12. Has Meta verification been initiated? This is the single biggest external
    schedule risk for Phase 2.

---

## 11. Unresolved Technical Items

These are open technical questions. Do not proceed with affected modules until resolved.

- **Hosting:** Option A/B/C not yet confirmed (see Section 8)
- **ConvoGenie integration:** API feasibility and integration scope unknown
- **Stock Excel format consistency:** Must be confirmed before building ingestion pipeline
- **SAP:** Now lower priority — daily Excel replaces direct SAP integration for
  Modules 4/5. But SAP pre-check still needed to confirm nothing else depends on it.
- **WhatsApp API approval:** Do not build WhatsApp ingestion until Meta approval confirmed.
- **Module 6 (Chatbot) tier:** Client has not confirmed tier. Do not finalize scope or fee.
- **Voice Stand-in:** Not greenlit. Do not plan or scaffold anything.
- **Corporate team roles:** Client said "not sure" — keeping lead + member for now. Confirm at next meeting.
- **LLM wiring:** `generate_quotation_draft` and `classify_message` in `quotations/services/llm.py` raise `NotImplementedError`. Full scaffold (system prompt, keyword injection, together.ai call structure) planned for next session. Wire actual API call once together.ai API key confirmed.
- **Product Excel structure:** User to share the pricing Excel — need to confirm column layout before finalising CSV upload view and `PricingEntry` field set.
- **Email dummy account:** Dummy Gmail to be configured in `TeamEmailConfig` for demo. Credentials will be provided by Janav — do not hardcode.

---

## 12. Fee Structure

**What has been quoted to client: ₹95,000 for 5 core modules.**

| Module                          | Fee            |
|---------------------------------|----------------|
| Base Setup                      | ₹5,000         |
| Quotation Automator             | ₹25,000        |
| Training + Case Solver          | ₹20,000        |
| Credit Risk AI                  | ₹20,000        |
| Lead Ranking + Inventory Intel  | ₹25,000        |
| **Core Total (quoted)**         | **₹95,000**    |
| Internal AI Chatbot             | TBD (pending ConvoGenie assessment) |
| AI Voice Stand-in               | Quoted separately by tier if greenlit |

All API/infrastructure costs (together.ai, WhatsApp Business API, Hetzner VPS,
domain, etc.) are borne by the client, not Janav.

---

## 13. Module Specifications

### Module 1 — Base Setup (₹5,000) — COMPLETE
Django project scaffold, PostgreSQL connection, CustomUser, full auth flow, `base.html`.
**Remaining:** role-based navigation in `base.html` (nav not yet gated by role).

---

### Module 2 — Quotation Automator (₹25,000) — Phase 2
**Purpose:** Parse incoming leads from WhatsApp, email, phone transcripts.
Match against master pricing sheet. Generate draft quotation using LLM.

**Inputs:**
- WhatsApp messages (WhatsApp Business API — Meta approval pending)
- Emails (IMAP polling)
- Phone call transcripts (deferred)

**Core logic:**
1. Ingest raw lead text
2. Call together.ai with tool use / function calling
3. LLM tools: look up master pricing sheet, apply discount rules, check stock
4. LLM returns structured quotation draft
5. Sales rep reviews and approves before sending

**Key dependency:** WhatsApp Business API Meta verification (1–3 weeks).
**Architecture:** Tool use / function calling. **Estimated effort:** 90–110 hrs.

---

### Module 3 — Training System + Case Solver (₹20,000) — Phase 3
**Purpose:** Sales staff Q&A on products, processes, past cases via static docs.
**Architecture:** RAG. Vector store: pgvector. Embeddings + generation: together.ai.
**Estimated effort:** 70–85 hrs.

---

### Module 4 — Credit Risk AI (₹20,000) — Phase 4
**Purpose:** Assess customer default risk before extending credit.
**Inputs:** Financial docs (PDF), GST returns, internal transaction history.
**Architecture:** Tool use / function calling.
**Estimated effort:** 60–75 hrs.

---

### Module 5 — Lead Ranking + Inventory Intelligence (₹25,000) — Phase 5
**Purpose:** Rank leads by conversion likelihood. Surface inventory insights.

**Data source (updated):** Daily Excel files ingested into PostgreSQL — NOT direct
SAP integration. Three files: Main Stock, Plate Stock, Rolling Stock.
See Section 7 for full data structure.

**Architecture:** Tool use / function calling. Django queries PostgreSQL (stock tables).
**Estimated effort:** 65–100 hrs (reduced uncertainty now that SAP is replaced by Excel).

---

### Module 6 — Internal AI Chatbot (fee TBD) — Phase 7
**Purpose:** Staff Q&A across all modules in natural language.
**Architecture:** Hybrid RAG + tool use.
**Tiers:**
- Tier 1 (2.5–3.5wk): RAG + tool use, simple Q&A
- Tier 2 (5–7wk): Multi-step conversational, session memory
- Tier 3: Claude Enterprise + MCP — configure, don't build

**Blocker:** ConvoGenie integration scope must be resolved first (see Section 9).
Do not finalize tier, fee, or scope until then.

---

### Module 7 — AI Voice Stand-in (proposed, NOT greenlit)
**Purpose:** AI answers calls when salesperson is busy, logs lead.
**Tiers:**
- Tier 1 (₹15K–20K): Voicemail-to-text + auto-reply
- Tier 2 (₹40K–60K): Real-time AI with generic voice
- Tier 3 (₹80K–1,20,000+): Cloned salesperson voice

**Legal risks (Tier 3):** Written consent for voice cloning, caller disclosure,
DPDPA 2023 compliance, IPC S.416 impersonation risk.

**Do NOT start any Voice Stand-in work until client greenlights a specific tier.**

---

## 14. Phased Delivery & Schedule

| Phase | Weeks      | Module                          | Hours Est. | Key Risks                       |
|-------|------------|---------------------------------|------------|---------------------------------|
| 1     | 1–2        | Base Setup                      | 40–50      | Complete                        |
| 2     | 3–7        | Quotation Automator             | 90–110     | WhatsApp API approval delay     |
| 3     | 8–11       | Training + Case Solver          | 70–85      | First RAG build                 |
| 4     | 12–15      | Credit Risk AI                  | 60–75      | PDF parsing reliability         |
| 5     | 16–18      | Lead Ranking + Inventory        | 65–100     | Excel format consistency        |
| 6     | +6–8wk     | Voice Stand-in (if greenlit)    | TBD        | Legal, Twilio/Meta approvals    |
| 7     | +2.5–3.5wk | Internal AI Chatbot             | 55–70      | ConvoGenie scope, tier TBD      |

**Contractual deadline:** ~September.
**College exam weeks** will reduce output — factor into schedule.

---

## 15. Architecture Decisions — Locked

Do not suggest alternatives unless Janav explicitly asks to reconsider.

1. **Tool use / function calling** for live-data modules (2, 4, 5, Chatbot live queries)
2. **RAG** for static modules (Training + Case Solver, Chatbot knowledge base). pgvector only.
3. **No local LLM.** together.ai is sole provider. No Ollama, llama.cpp, etc.
4. **No MCP server.** Django-native tool use.
5. **No separate vector database.** pgvector in PostgreSQL only.
6. **Bootstrap 5 + Django templates.** No JavaScript framework.
7. **Deployment:** Pending hosting decision (see Section 8). If Option B: Gunicorn + Nginx
   on Linux VPS. If Option A/C: IIS + Waitress on Windows Server.
8. **Stock data:** Excel is transport only. PostgreSQL is destination. No live SAP calls.
9. **Two-step LLM ingestion flow:** Every inbound message (email or WhatsApp) goes through `classify_message(text)` first. If not an inquiry, discard silently — do not create a lead. Only then call `generate_quotation_draft`. Email also pre-filtered by headers before hitting the LLM.
10. **ProductKeyword model:** Company-specific client terms stored in PostgreSQL, admin-editable. Fetched at call time and injected into the LLM system prompt — not hardcoded in code.
11. **lookup_pricing returns `found: bool`:** Tool always returns `{"found": true/false, "results": [...]}`. Not-found items are included in the quotation draft with `unit_price=0` and `notes="Price not found — fill manually"` — never silently dropped.
12. **Team-scoped views:** All summary views (customer list, lead list, quotation list) default to showing the requesting user's team data. Admin and `?scope=all` query param shows all records. Leads/admins see the handover button on customer records.

---

## 16. Project Root & Directory Structure

```
ferite_steel/                      ← project root
│
├── ferite_steel/                  ← Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── aegis/                         ← auth & user management
│   ├── models.py                  ← CustomUser (team + role fields)
│   ├── views.py                   ← dashboard, add_user, directory, edit_role, register, approve, delete
│   ├── forms.py                   ← AddUserForm, EditRoleForm (both include team field)
│   └── urls.py
│
├── quotations/                    ← Module 2
│   ├── models.py                  ← Customer, PricingEntry, Broker, Lead, Quotation, QuotationLineItem, MarketOrder
│   │                                 + ProductKeyword, TeamEmailConfig, Customer.handling_team (planned)
│   ├── views.py                   ← all quotation, lead, broker, and market order views
│   │                                 + customer_list, customer_detail, customer_handover,
│   │                                   product_list, product_upload (planned)
│   ├── forms.py                   ← ManualLeadForm, QuotationEditForm, LineItemFormSet,
│   │                                 BrokerForm, MarketOrderForm, MarketOrderRateForm,
│   │                                 MarketOrderAssignForm, MarketOrderDOForm
│   │                                 + CustomerHandoverForm, ProductUploadForm (planned)
│   ├── admin.py                   ← Customer, Broker, MarketOrder, Lead, Quotation registered
│   │                                 + ProductKeyword, TeamEmailConfig (planned)
│   ├── urls.py
│   ├── management/
│   │   └── commands/
│   │       └── poll_emails.py     ← IMAP ingestion: header filter → classify → create Lead (planned)
│   └── services/
│       ├── llm.py                 ← generate_quotation_draft(lead, entity_notes) — stub + scaffold planned
│       │                             classify_message(text) — stub (planned)
│       │                             _build_keyword_context() — fetches ProductKeyword (planned)
│       └── tools/
│           └── pricing.py         ← lookup_pricing tool — returns found: bool + results
│
├── templates/                     ← global templates (all extend base.html)
│   ├── base.html                  ← nav gated by role; team badge in user menu
│   ├── dashboard.html             ← + New Lead / + New Quotation / + Market Order buttons
│   ├── add_user.html              ← includes JS team→role filter
│   ├── edit_user_role.html        ← includes JS team→role filter
│   ├── registration/              ← login, password reset
│   └── quotations/
│       ├── lead_list.html
│       ├── lead_detail.html
│       ├── lead_create.html
│       ├── quotation_list.html    ← Outcome column (Win/Loss/—)
│       ├── quotation_detail.html  ← Revise, Send/Internal Copy, Edit, PDF, Outcome, Versions
│       ├── quotation_edit.html    ← inline formset + JS auto-calc
│       ├── quotation_pdf.html     ← WeasyPrint A4; "INTERNAL — RATES ONLY" header for broker quotations
│       ├── quotation_select_lead.html
│       ├── broker_list.html
│       ├── broker_create.html
│       ├── market_order_list.html
│       ├── market_order_create.html
│       ├── market_order_detail.html  ← 4-step flow: rate → confirm → assign DO → DO number
│       ├── customer_list.html        ← team-scoped + ?scope=all toggle (planned)
│       ├── customer_detail.html      ← history + handover button (planned)
│       ├── product_list.html         ← PricingEntry catalog (planned)
│       └── product_upload.html       ← CSV upload form, admin only (planned)
│
├── .claude/
│   ├── settings.json
│   └── commands/
│       └── md-write.md            ← /md-write command definition
│
├── CLAUDE.md                      ← this file
├── manage.py
└── requirements.txt
```

**Shell context:** Working directory is the project root unless stated.
Use `python manage.py` not `python3 manage.py`.

---

## 17. URLs Defined

**aegis** (prefix: `/`):

| URL                                        | View / Name            |
|--------------------------------------------|------------------------|
| `/login/`                                  | LoginView              |
| `/logout/`                                 | LogoutView             |
| `/dashboard/`                              | dashboard              |
| `/register/`                               | register               |
| `/add-user/`                               | add_user (admin only)  |
| `/directory/`                              | user_directory (admin) |
| `/directory/<id>/edit-role/`               | edit_user_role (admin) |
| `/approve-user/<id>/`                      | approve_user (admin)   |
| `/delete-user/<id>/`                       | delete_user (admin)    |
| `/password-reset/`                         | PasswordResetView      |
| `/password-reset/done/`                    | PasswordResetDoneView  |
| `/password-reset/confirm/<uid>/<token>/`   | PasswordResetConfirmView |
| `/password-reset/complete/`                | PasswordResetCompleteView |

**quotations** (prefix: `/quotations/`):

| URL                                           | View / Name                  |
|-----------------------------------------------|------------------------------|
| `/quotations/`                                | quotation_list               |
| `/quotations/select-lead/`                    | quotation_select_lead        |
| `/quotations/create/<lead_pk>/`               | quotation_create             |
| `/quotations/<pk>/`                           | quotation_detail             |
| `/quotations/<pk>/edit/`                      | quotation_edit               |
| `/quotations/<pk>/pdf/`                       | quotation_pdf                |
| `/quotations/<pk>/approve/`                   | quotation_approve            |
| `/quotations/<pk>/outcome/`                   | quotation_outcome            |
| `/quotations/<pk>/revise/`                    | quotation_revise             |
| `/quotations/<pk>/send/`                      | quotation_send               |
| `/quotations/leads/`                          | lead_list                    |
| `/quotations/leads/create/`                   | lead_create                  |
| `/quotations/leads/<pk>/`                     | lead_detail                  |
| `/quotations/brokers/`                        | broker_list                  |
| `/quotations/brokers/create/`                 | broker_create                |
| `/quotations/market-orders/`                  | market_order_list            |
| `/quotations/market-orders/create/`           | market_order_create          |
| `/quotations/market-orders/<pk>/`             | market_order_detail          |
| `/quotations/market-orders/<pk>/set-rate/`    | market_order_set_rate        |
| `/quotations/market-orders/<pk>/confirm/`     | market_order_confirm         |
| `/quotations/market-orders/<pk>/assign-do/`   | market_order_assign_do       |
| `/quotations/market-orders/<pk>/set-do/`      | market_order_set_do          |
| `/quotations/customers/`                      | customer_list (planned)      |
| `/quotations/customers/<pk>/`                 | customer_detail (planned)    |
| `/quotations/customers/<pk>/handover/`        | customer_handover (planned)  |
| `/quotations/products/`                       | product_list (planned)       |
| `/quotations/products/upload/`                | product_upload (planned)     |

**admin**: `/admin/` — jazzmin-themed Django admin.

---

## 18. App Structure

| App          | Purpose                                                                        |
|--------------|--------------------------------------------------------------------------------|
| `aegis`      | Auth & user management — CustomUser                                            |
| `quotations` | Module 2 — Lead, Quotation, PricingEntry, Broker, MarketOrder, LLM service    |
| `ares`       | Not yet created                                           |
| `athena`     | Not yet created                                           |
| `hephaestus` | Not yet created                                           |
| `hermes`     | Not yet created                                           |
| `themis`     | Not yet created                                           |

Future apps to create per module: `credit_risk`, `training`, `leads`.

---

## 19. External Services Status

| Service               | Status                          | Notes                                        |
|-----------------------|---------------------------------|----------------------------------------------|
| together.ai           | Active — Janav has access       | Primary LLM for all modules                  |
| WhatsApp Business API | Pending Meta approval           | Client must initiate — do NOT assume live     |
| ConvoGenie            | Client has account — reviewing  | Integration scope TBD (see Section 9)        |
| SAP                   | Deprioritised                   | Daily Excel replaces direct integration      |
| Email (IMAP/SMTP)     | Planned — dummy Gmail for demo  | Dummy account (to be deleted post-demo); poll_emails command planned |
| Hetzner VPS           | Not provisioned                 | Pending hosting decision                     |
| Twilio/Deepgram/ElevenLabs | Not started               | Only if Voice Stand-in greenlit              |

---

## 20. Settings & Configuration

- `LOGIN_REDIRECT_URL = '/dashboard/'`
- `LOGIN_URL = '/login/'`
- `LOGOUT_REDIRECT_URL = '/login/'`
- Templates: `<project_root>/templates/` — configured via `BASE_DIR / 'templates/'`
- Static files: served by `whitenoise` in both dev and production (`STATICFILES_STORAGE = CompressedManifestStaticFilesStorage`)
- `DEBUG = False` in production — never deploy with DEBUG = True
- Secret key from environment variable only — never hardcoded

### Environment variables (.env — never commit)
```
SECRET_KEY=
DEBUG=
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=
TOGETHER_API_KEY=
```

---

## 21. Coding Conventions

- One Django app per major module
- Models: always use `class Meta` with `verbose_name` and `verbose_name_plural`
- Views: CBVs for CRUD, FBVs for custom logic
- All LLM calls through a single service layer (`services/llm.py`) — never call
  together.ai directly from views
- Tool definitions for function calling go in `services/tools/`
- Environment variables via `python-dotenv` + `os.environ` (NOT python-decouple)
- Requirements pinned (`pip freeze > requirements.txt` after each install)

---

## 22. Non-Negotiables

- Never suggest running a local LLM or downloading model weights
- Never suggest Pinecone, Qdrant, Weaviate, Chroma — pgvector only
- Never commit secrets to version control
- Never deploy with DEBUG = True
- Never skip migration review before applying
- Never add a frontend JavaScript framework
- Never build Voice Stand-in until client greenlights a specific tier
- Never assume WhatsApp API is live — always check with Janav first
- Never quote Module 6 fee until ConvoGenie scope is resolved
