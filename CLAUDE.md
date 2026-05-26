# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

# FERITE-STEEL — Claude Code Project Context

This file is the single source of truth for all Claude tools (Claude Code, Cowork,
Claude.ai) on every aspect of the FERITE-STEEL project. Read it fully before doing
anything. Never deviate from the decisions recorded here without explicit instruction
from Janav.

**Last updated:** 27 May 2026 (session 12)

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
python manage.py runserver
python manage.py makemigrations  # always review output before migrating
python manage.py migrate
python manage.py test
python manage.py test aegis
python manage.py test quotations
python manage.py createsuperuser
python manage.py collectstatic
```

**Together.ai SDK installed** (`together==2.14.0`). `generate_quotation_draft` is fully wired.

---

## 1. Project Overview

FERITE-STEEL is a Django-based CRM and business management system for an iron and steel
distribution company. Replaces manual quoting, gut-feel credit decisions, unstructured
lead management, and slow salesperson onboarding with an automated, AI-assisted web system.

Paid client engagement managed solely by Janav (second-year student). Trust built
incrementally through phased delivery. Every architectural decision must be defensible
to a non-technical client.

**Modules:** 1. Base Setup (complete) · 2. Quotation Automator · 3. Training + Case Solver ·
4. Credit Risk AI · 5. Lead Ranking + Inventory Intelligence · 6. Internal AI Chatbot (fee TBD) ·
7. AI Voice Stand-in (proposed, NOT greenlit)

---

## 2. Developer Profile & Communication Rules

- Janav is the **sole developer**. There is no team.
- Second-year student, no prior real-world project experience.
- Prefers **granular, step-by-step explanations** — never skip steps or assume prior knowledge.
- When giving terminal commands, always **specify which directory** and expected output.
- When multiple approaches exist, **explain tradeoffs before recommending**.
- Prefers **direct, honest assessments** including unflattering ones — do not soften evaluations.
- **Working style:** Act as advisor/helper only. Guide Janav to figure things out himself first.
  Do not give direct answers unless he has tried and asked multiple times.

---

## 3. Current State

**Phase 1 complete. Phase 2 (Quotation Automator): quotation UI/flow done; LLM draft generation wired; classify_message + classify_broker_response built; email send (SMTP) built; poll_emails command built with --scheduled flag and in-app Poll Inbox button. Broker-to-DO pipeline complete. WhatsApp ingestion pending Meta approval.**
**Current work: module-3 branch — broker pipeline + poll timer built this session.**

### What is built

**Auth & Users:** Full auth flow (login/logout/register/password reset). CustomUser with `team` + `role`. User management (add/edit/approve/delete) admin-gated. JS role filter in add/edit user forms. Nav gated by role; Database dropdown (Customers/Products/Brokers for market/admin). Dashboard stats scoped by role (admin/lead see all; member sees own). Market Order button visible to market + admin only.

**Product catalog:** 523 rows imported from client Excel (rates all 0 — fill via admin). Grouped view — rows by sub_type+size; cascading dropdowns Make→Length→Grade→Site; text search only. Relational pricing: `base_product` self-FK + `rate_offset`; `effective_rate` = base rate + offset (or own rate). No chaining — derived products always point directly to a base. `_build_product_groups()` used by product list + catalog JSON at `/database/products/catalog.json`.

**Customer & Broker:** Customer list team-scoped. 6,414 SAP records imported (`import_business_partners.py`); upsert key = `customer_code`. Customer auto-upserted on every quotation save. Broker CRUD at `/database/brokers/`.

**Lead flow:** List/create/detail/delete with cascade warning modal. Fields: company, industry, location, broker FK (optional; set for market team leads).

**Quotation flow:** Edit form with inline formset + JS auto-calc. WeasyPrint PDF. Versioning — Revise creates v2/v3 cloned from current. Outcome (Win/Loss/Not Updated) stored on root, shared across versions. Win records exact winning version via `winning_quotation` FK. Stock deduction on first Win only — one-time, irreversible (`stock_deducted` guard). Approve: lead + admin only. Broker-sourced quotations (`lead.broker ≠ null`): PDF = "INTERNAL — RATES ONLY"; text-only rate email.

**Quotation line item picker:** "⌕ pick" button → accordion modal with full grouped catalog. Fills product FK, make, length, HSN, purchase rate. `make` + `length` readonly (picker only). `pcs` readonly+greyed when product has no pieces.

**Pricing add-ons:** 7 per-row collapsible inputs (Parity/Cutting/Loading/Transport/Margin/Interest/Commission) under "⊞ add-ons". Session-only — defaults read from `customer.notes` (`--- Pricing Add-ons ---` section) at page load; NOT written back on save. Only `unit_price` persisted. UOM (ton/kg) per line item. `discount_pct` per line item; `final_price` = `total_price × (1 − pct/100)` — used for discount-aware taxes/grand total. `floatformat:2` applied globally.

**Stock deduction on Win:** `_deduct_stock()` called once via `stock_deducted` guard. Deducts quantity (converted to tons if uom=kg) using `Greatest(F('quantity') - qty, 0)` — atomic, never negative. Skips line items without `product` FK (LLM-generated items).

**LLM / AI:** `generate_quotation_draft(lead, entity_notes)` in `quotations/services/llm.py` — tool-use loop with `lookup_pricing`, ProductKeyword injection, UOM context, reply-chain focus in system prompt. Graceful fallback to blank editor. `classify_message(text)` — YES/NO classifier for inbound messages. `classify_broker_response(text)` — returns `'confirmation'`/`'counter'`/`'other'` for broker replies. Shared `together_client` in `ferite_steel/ai.py`.

**Email pipeline:** `poll_emails` management command — IMAP per TeamEmailConfig, spam pre-filter, broker reply detection (`_find_broker`), classify_message, Lead + MarketOrder creation for broker senders, marks Seen. `--dry-run` flag. `--scheduled` flag throttles by `TeamEmailConfig.poll_interval_minutes`; stamps `last_polled_at` after each real run. "Poll Inbox" button on lead list (admin/lead only) hits `poll_emails_now` view. Cron: `* * * * * manage.py poll_emails --scheduled`. `_strip_reply_chain()` handles Gmail/Outlook/forwarded formats. `quotation_send` — compose/confirm form, SMTP send, PDF attach (non-broker), text-only rate email for broker leads. SMTP host = `imap_host.replace("imap.", "smtp.")`.

**Broker-to-DO pipeline:** `_find_broker(email_addr)` matches inbound sender to active Broker. Broker email → Lead (with broker FK) + MarketOrder auto-created. Broker reply → `classify_broker_response()` → if confirmation: MarketOrder status → `broker_confirmed`, `broker_confirmed_at` stamped; if counter: reply appended to Lead notes. `notify_loading_dock` signal on `MarketOrder` post_save — fires only when `status` field transitions to `broker_confirmed`, emails `loading_dock_member`. DO send: `market_order_do_send` view + template — user enters DO number, gets compose/confirm UI, sends text to broker email. MarketOrder status → `completed` on send. `lead` FK added to `MarketOrder`.

**Market team:** MarketOrder full flow (`new`→`rate_sent`→`broker_confirmed`→`do_pending`→`completed`). Visual pipeline timeline on detail page (numbered nodes, connector line, state-aware colours). Separate from Quotation — tracks logistics, not pricing.

### What is NOT yet built (planned for next session)
- **Pagination** (urgent) — customer (6,400+), lead, quotation lists need `Paginator` before go-live
- **`django.contrib.humanize` `intcomma`** — ₹ values should display as ₹50,00,000 not ₹5000000
- **`transaction.atomic()`** on `quotation_outcome` — stock deduction + outcome save must be atomic
- **Django permissions signal** — `post_save` on CustomUser to auto-assign role permissions (Architecture Decision 18)
- **Customer handover view** (`customer_handover`) — `handling_team` field exists, view not built
- Email ingestion live test — needs dummy Gmail App Password in `TeamEmailConfig` admin (Janav to provide; delete post-demo)
- WhatsApp ingestion — deferred until Meta approval confirmed
- Product rates — all 0 after import; must be filled via admin
- TMT products missing — must be added manually or re-imported
- `from datetime import timedelta` in `poll_emails.py` should be moved to top-level imports (currently inside `handle`)

### Pending before Phase 2 is fully live
- WhatsApp Business API Meta approval
- Dummy Gmail credentials in `TeamEmailConfig`
- Hetzner VPS provisioning + cron setup for `poll_emails --scheduled`

---

## 4. Tech Stack

### Backend
- **Framework:** Django 6.0.3 · **Python:** 3.12 · **Database:** PostgreSQL 16 (`ferite_steel_db`)
- **ORM:** Django ORM only — no raw SQL unless unavoidable
- **Packages:** `psycopg2-binary`, `python-dotenv`, `whitenoise`, `django-jazzmin`, `together==2.14.0`

### Frontend
- **CSS:** Bootstrap 5 · **Templating:** Django templates (NOT Jinja2) · No JS framework

### Server (On-Premise)
Windows Server 2016 — Intel Xeon Bronze 3106, 32 GB RAM, 4 TB HDD, **no GPU**

### Hosting (DECISION PENDING — see Section 8)
Option A: Windows Server via IIS + static IP · Option B (recommended): Hetzner VPS + Gunicorn + Nginx · Option C: Cloudflare Tunnel

### AI / LLM
- **Provider:** together.ai only. No local models, no Ollama.
- Tool use → live-data modules (2, 4, 5, Chatbot queries). RAG → static modules (3, Chatbot KB).
- No MCP server. No separate vector DB (pgvector in PostgreSQL only).

### Database Tools
DataGrip 2025.1.3 (primary), pgAdmin 4 (secondary)

---

## 5. Team & Employee Structure

| Team slug | Display name | Roles |
|-----------|--------------|-------|
| `team_9` | Team 9 | `lead`, `member` (IndiaMART/JustDial/TradeIndia/BNL leads) |
| `cs` | CS Team | `lead`, `member` (customer service, jointly handled) |
| `market` | Market Team | `lead`, `primary`, `rolling`, `loading_dock` |
| `corporate` | Corporate Team | `lead`, `member` (details TBD) |

Admins: `team = null`. Role dropdown in Add/Edit User forms filters via JS based on selected team.

**Market team workflow:** Broker sends order → market member creates Lead + MarketOrder → quotation editor used internally (rate calc; PDF = "INTERNAL — RATES ONLY") → rate sent to broker → broker confirms → loading dock assigned → DO issued.

---

## 6. Models

### CustomUser (aegis)
`role`: admin/lead/member/primary/rolling/loading_dock (default: member). `team`: team_9/cs/market/corporate (nullable for admins). Also: `phone`, `branch`, `employee_id`.

### Product (database)
523 imported rows; rates all 0. Fields: `category` (main/rolling/plate), `make` (manufacturer, 14 choices, blank for existing rows), `sub_type` (angle/channel/ub/uc/beam/flat/red_material/tmt), `size`, `length` (24 choices), `grade` (27 choices), `godown`, `site` (site_1/site_2), `quantity` (T), `rate` (₹/T), `pieces`, `hsn_code`, `is_active`.

**Relational pricing:** `base_product` self-FK (SET_NULL, nullable) + `rate_offset` (default 0). `effective_rate` property = `base_product.rate + rate_offset` if base set, else own `rate`. No chaining — derived products always point to a base directly, never to another derived product.

`_build_product_groups(queryset)` in `database/views.py` — nested dict: sub_type+size → category → length → grade → site → {id, rate, qty, hsn, godown, pieces}. Uses `select_related('base_product')` and `effective_rate`. Used by product list and catalog JSON.

### Customer (database)
6,414 SAP records + auto-upserted on quotation save. Upsert key: `customer_code`.
Fields: `customer_code`, `name`, `company`, `phone`, `email`, `gst_number`, `pan_number`, `msme_number`, `city`, `pincode`, `billing_address`, `shipping_address`, `payment_terms` (advance/cash), `type_of_business` (C/I/G), `is_active`, `sap_created_at`, `transport_extra`, `loading_rate` (default 0.5 ₹/T), `notes` (AI context + `--- Pricing Add-ons ---` section — read at page load, NOT written back on save), `competitors`, `rm` FK, `handling_team`.

### Broker (database)
`name`, `company`, `location`, `phone`, `email`, `notes`, `is_active`. Separate from Customer — different flow direction (broker sends orders, no transport cost memory).

### Lead (quotations)
`customer_name`, `customer_phone`, `customer_email`, `company`, `industry`, `location`, `broker` FK (nullable), `raw_text`, `notes`, `source`, `status`, `created_by`, `created_at`.

### Quotation (quotations)
`quotation_number` (auto: `QT-00001`, `QT-00001-v2`), `lead` FK, `version`, `parent_quotation` self-FK (null = root), `status` (draft/approved/sent), `outcome` (win/loss/not_updated — root only, shared across versions), `winning_quotation` self-FK (records exact version that won — see Architecture Decision 14), `stock_deducted` (guards one-time deduction — see Architecture Decision 15), `payment_terms`, `delivery_address`, `transport_extra`, `sgst_percent`, `cgst_percent`, `total_amount`, `valid_until`, `llm_raw_response`.

Broker-sourced (`lead.broker ≠ null`): PDF = "INTERNAL — RATES ONLY".

### QuotationLineItem (quotations)
`quotation` FK, `product` FK (nullable/SET_NULL — NULL for LLM-generated items; must be picker-set for stock deduction to work), `product_name`, `make` (readonly — picker only), `length` (readonly — picker only), `pcs` (readonly+greyed when no pieces), `uom` (ton/kg), `quantity` (3dp), `unit_price` (readonly — JS-calculated from purchase_rate + add-ons), `total_price` (server-side), `discount_pct` (default 0), `notes`.

`final_price` property = `total_price × (1 − discount_pct/100)` — used in `_quotation_context` so taxes and grand total are discount-aware.

### MarketOrder (quotations)
`broker` FK (CASCADE), `quotation` FK (nullable), `sub_team` (primary/rolling), `product_details`, `quantity`, `status` (new/rate_sent/broker_confirmed/do_pending/completed/cancelled), `rate`, `loading_dock_member` FK, `do_number`, `notes`, `created_by`.

### ProductKeyword (quotations)
Maps client trade terms (e.g. "sariya") → canonical product names. `keyword`, `maps_to`, `notes`, `is_active`. `_build_keyword_context()` fetches active keywords and injects them into the LLM system prompt on every draft generation call.

### MarketOrder (quotations)
`broker` FK (CASCADE), `lead` FK (SET_NULL, nullable — set when order auto-created from inbound email), `quotation` FK (nullable), `sub_team` (primary/rolling), `product_details`, `quantity`, `status` (new/rate_sent/broker_confirmed/do_pending/completed/cancelled), `rate`, `loading_dock_member` FK, `do_number`, `notes`, `created_by`. `notify_loading_dock` post_save signal fires email to `loading_dock_member` when `status` transitions to `broker_confirmed` (guarded by `update_fields`).

### TeamEmailConfig (quotations)
IMAP credentials per team (unique per team). `team`, `email_address`, `imap_host` (default imap.gmail.com), `imap_username`, `imap_password`, `imap_port` (993), `use_ssl`, `is_active`, `poll_interval_minutes` (default 30), `last_polled_at` (stamped after each real poll run). SMTP host derived at send time: `imap_host.replace("imap.", "smtp.")`.

`AUTH_USER_MODEL = 'aegis.CustomUser'`
**Migration discipline:** Never run `migrate` without reviewing `makemigrations` output first.

---

## 7. Inventory & Stock Data

Client receives 3 Excel files daily via WhatsApp:
1. `Main_Stock.xlsx` — Angle, Channel, Beam, NPB, WPB, TMT, Red Material. Sheet name = date (e.g. `01-04`). Categories laid out horizontally side by side.
2. `New_Plate_Stock.xlsx` — Plate stock by plot/location (Plot 557, 558, 560). Tracks grade (E250/E350), pieces, heat numbers, vehicle numbers.
3. `Stock_Rolling_New.xlsx` — Rolling Angle, Channel, Beam, Flat, TMT rods, Square.

**Architecture:** Excel is transport only. PostgreSQL is the destination. Excel arrives → Django parses (openpyxl/pandas) → data upserted into PostgreSQL → file discarded. All downstream modules query the database, not files.

---

## 8. Hosting Decision

**Status: CONFIRMED — Option B (Hetzner VPS + Gunicorn + Nginx). Confirmed 24 May 2026.**

Client confirmed comfort with business data hosted off-premise. VPS not yet provisioned — next step is to spin up Hetzner CX22 and run the deployment setup.

**Deployment stack:**
- Server: Hetzner CX22 VPS, Ubuntu 24.04
- WSGI: Gunicorn
- Reverse proxy: Nginx
- SSL: Let's Encrypt via Certbot
- Database: PostgreSQL on the same VPS
- Static files: WhiteNoise (already wired in `settings.py`)
- PDF: WeasyPrint — works natively on Linux via `apt install libpango-1.0-0 libcairo2`
- Scheduled tasks: `poll_emails --scheduled` via cron every minute (throttled by `TeamEmailConfig.poll_interval_minutes`)

**Pre-deployment checklist (not yet done):**
- Set `ALLOWED_HOSTS` to domain/IP in settings
- Set all env vars on VPS (SECRET_KEY, DB_*, TOGETHER_API_KEY)
- Run `collectstatic` and `migrate` on first deploy
- Configure systemd service for Gunicorn
- Set up cron for `poll_emails`
- Obtain domain and point DNS to VPS IP

---

## 9. ConvoGenie

convogenie.ai — no-code AI chatbot platform (FAQs, basic support, no business data access). Client has already paid for it and asked whether FERITE-STEEL can integrate with it.

**Current state:** Janav has account access. Client met ConvoGenie on 11 May 2026. Integration scope + API feasibility still TBD pending meeting outcome.

**Key distinction:** ConvoGenie = generic no-code chatbot. Module 6 = purpose-built with live pricing, credit risk, inventory queries — entirely different capability.

**Do not quote Module 6 fee until ConvoGenie integration scope is resolved.**

---

## 10. Client Questions (To Ask at Next Meeting)

1. All 523 product rates are 0 — provide a rate file or fill via admin.
2. Who/what generates the daily Excel stock files — manual entry or auto-generated?
3. Are all 3 files (Main Stock, Plate, Rolling) updated daily, or just some?
4. Is the column layout identical every day, or does it occasionally vary?
5. Does the file arrive fresh each day, or as a new sheet in the same workbook?
6. What are the specific roles within the Corporate team?
7. ~~Is client comfortable with business data on a cloud server?~~ RESOLVED — Option B confirmed.
8. ~~Does client's office have a static IP?~~ No longer relevant — using Hetzner VPS.
9. What did ConvoGenie say about API access and integration options?
10. What plan is client on — does it include API access?
11. What does client actually want the two systems to do together?
12. Has Meta verification been initiated for WhatsApp Business API?

---

## 11. Unresolved Technical Items

Do not proceed with affected modules until resolved.

- **Hosting:** RESOLVED — Option B (Hetzner VPS). VPS not yet provisioned (see Section 8).
- **ConvoGenie integration:** API feasibility and scope unknown (see Section 9)
- **WhatsApp API approval:** Do not build ingestion until Meta confirms
- **Module 6 (Chatbot) tier:** Not confirmed. Do not finalize scope or fee
- **Voice Stand-in:** Not greenlit. Do not plan or scaffold anything
- **Corporate team roles:** TBD — placeholder is lead + member
- **Stock Excel format consistency:** Must be confirmed before building Module 5 ingestion pipeline
- **SAP:** Deprioritised — daily Excel replaces direct integration. Confirm no other dependencies
- **`bulk_create`/`bulk_update`** for Module 5 stock import: plan from the start; no individual `.save()` calls
- **Model-level validators:** GST (15-char) and PAN (10-char) fields need `RegexValidator`
- **Django logging config:** Must write errors to file before production — currently silent on 500
- **Audit logging:** Consider `django-auditlog` or `django-simple-history` for Module 4 (Credit Risk)

---

## 12. Fee Structure

**Quoted: ₹95,000 for 5 core modules.** All API/infrastructure costs borne by client.

| Module | Fee |
|--------|-----|
| Base Setup | ₹5,000 |
| Quotation Automator | ₹25,000 |
| Training + Case Solver | ₹20,000 |
| Credit Risk AI | ₹20,000 |
| Lead Ranking + Inventory Intel | ₹25,000 |
| **Core Total** | **₹95,000** |
| Internal AI Chatbot | TBD (pending ConvoGenie assessment) |
| AI Voice Stand-in | TBD by tier if greenlit |

---

## 13. Module Specifications

### Module 1 — Base Setup (₹5,000) — COMPLETE
Django scaffold, PostgreSQL, CustomUser, full auth flow, base.html.

### Module 2 — Quotation Automator (₹25,000) — Phase 2 (current)
Parse leads from WhatsApp/email, match pricing, generate LLM draft quotation for salesperson review. Architecture: tool use + function calling. Key dependency: WhatsApp Meta approval (1–3 weeks). Effort: 90–110 hrs.

### Module 3 — Training + Case Solver (₹20,000) — Phase 3
Staff Q&A on products/processes via static docs. Architecture: RAG, pgvector, together.ai. Effort: 70–85 hrs.

### Module 4 — Credit Risk AI (₹20,000) — Phase 4
Assess customer default risk before extending credit. Inputs: PDFs, GST returns, internal transaction history. Architecture: tool use. Effort: 60–75 hrs.

### Module 5 — Lead Ranking + Inventory Intelligence (₹25,000) — Phase 5
Rank leads by conversion likelihood. Surface inventory insights. Data source: daily Excel → PostgreSQL (see Section 7). Architecture: tool use. Effort: 65–100 hrs.

### Module 6 — Internal AI Chatbot (TBD) — Phase 7
Staff Q&A across all modules in natural language. Architecture: hybrid RAG + tool use.
Tiers: 1 (simple Q&A, 2.5–3.5wk) / 2 (conversational + session memory, 5–7wk) / 3 (Claude Enterprise + MCP, configure only).
Blocker: ConvoGenie scope must be resolved first. Do not finalize tier, fee, or scope until then.

### Module 7 — AI Voice Stand-in (NOT greenlit)
Tiers: 1 (₹15K–20K, voicemail-to-text) / 2 (₹40K–60K, real-time AI) / 3 (₹80K–1.2L, cloned voice).
Tier 3 legal risks: written consent for voice cloning, DPDPA 2023 compliance, IPC S.416 impersonation.
**DO NOT START any Voice Stand-in work until client greenlights a specific tier.**

---

## 14. Phased Delivery & Schedule

| Phase | Module | Hours Est. | Key Risks |
|-------|--------|------------|-----------|
| 1 | Base Setup | 40–50 | Complete |
| 2 | Quotation Automator | 90–110 | WhatsApp API approval delay |
| 3 | Training + Case Solver | 70–85 | First RAG build |
| 4 | Credit Risk AI | 60–75 | PDF parsing reliability |
| 5 | Lead Ranking + Inventory | 65–100 | Excel format consistency |
| 6 | Voice Stand-in (if greenlit) | TBD | Legal, Twilio/Meta approvals |
| 7 | Internal AI Chatbot | 55–70 | ConvoGenie scope, tier TBD |

**Contractual deadline:** ~September. Factor in college exam weeks.

---

## 15. Architecture Decisions — Locked

Do not suggest alternatives unless Janav explicitly asks to reconsider.

1. **Tool use / function calling** for live-data modules (2, 4, 5, Chatbot live queries)
2. **RAG** for static modules (Training + Case Solver, Chatbot knowledge base). pgvector only.
3. **No local LLM.** together.ai is sole provider. No Ollama, llama.cpp, etc.
4. **No MCP server.** Django-native tool use.
5. **No separate vector database.** pgvector in PostgreSQL only.
6. **Bootstrap 5 + Django templates.** No JavaScript framework.
7. **Deployment:** Hetzner CX22 VPS, Ubuntu 24.04. Gunicorn + Nginx. Let's Encrypt SSL. PostgreSQL on same VPS. (Confirmed 24 May 2026 — see Section 8.)
8. **Stock data:** Excel is transport only. PostgreSQL is destination. No live SAP calls.
9. **Two-step LLM ingestion flow:** Every inbound message goes through `classify_message(text)` first. If not an inquiry, discard silently — do not create a lead. Only then call `generate_quotation_draft`. Email also pre-filtered by headers before hitting the LLM.
10. **ProductKeyword model:** Company-specific client terms stored in PostgreSQL, admin-editable. Fetched at call time and injected into the LLM system prompt — not hardcoded in code.
11. **lookup_pricing returns `found: bool`:** Tool always returns `{"found": true/false, "results": [...]}`. Not-found items included in draft with `unit_price=0` and `notes="Price not found — fill manually"` — never silently dropped.
12. **Team-scoped views:** All summary views default to the requesting user's team data. Admin and `?scope=all` shows all records. Leads/admins see handover button on customer records.
13. **Shared AI client:** `ferite_steel/ai.py` holds the single `together_client`. All service layers import from there — never instantiate `Together(...)` directly in a service or view. If a new app needs LLM access, import from `ferite_steel.ai`.
14. **Win tracks the specific version, not just the lead:** `winning_quotation` FK is set to the exact `Quotation` instance the user marks as won — not the root. A lead may have 3 revisions; the salesperson picks which one closed the deal.
15. **Stock deduction is one-time and irreversible per deal:** `stock_deducted` guards against repeat deduction. Changing outcome away from Win and back does NOT re-deduct. Stock is never restored on outcome change (Loss/Not Updated after Win). Physical stock has already moved.
16. **Per-row pricing add-ons are session-only:** The 7 add-on inputs live only in the browser. Defaults read from `customer.notes` on page load; NOT written back on save. Never stored in any model field. Only `unit_price` persisted.
17. **Product FK on QuotationLineItem is set only via the picker:** LLM fills product_name as free text and never sets `product` FK. Stock deduction skips any line item without `product_id`. Salesperson must re-pick after LLM draft to link FK and enable stock tracking.
18. **Django custom permissions + role signal for access control:** Feature gates use Django's built-in permission system (`user.has_perm('app.codename')`), not hardcoded role string checks. Custom permissions declared in each model's `Meta.permissions`. `post_save` signal on `CustomUser` auto-assigns the baseline permission set whenever role is set/changed. Admin can grant extra permissions without a code change. Team-scoping (queryset filtering) remains code — permissions don't apply there. New models: define permissions in `Meta` from the start. Existing role checks: replace gradually as views are touched, not as a dedicated refactor.

---

## 16. Project Root & Directory Structure

```
ferite_steel/                      ← project root
├── ferite_steel/                  ← Django project config
│   ├── settings.py, urls.py, wsgi.py
│   └── ai.py                      ← shared together_client; import here, never instantiate elsewhere
├── aegis/                         ← auth & user management (CustomUser)
│   ├── models.py, views.py, forms.py, urls.py
├── database/                      ← Product, Customer, Broker + CRUD views
│   ├── models.py, views.py, forms.py, admin.py, urls.py
│   └── migrations/                ← 0001–0016
├── quotations/                    ← Module 2
│   ├── models.py                  ← Lead, Quotation, QuotationLineItem, MarketOrder, ProductKeyword, TeamEmailConfig
│   ├── views.py                   ← _parse_addon_notes(), _deduct_stock(), _quotation_context(), all views
│   ├── forms.py, admin.py, urls.py
│   ├── management/commands/poll_emails.py   ← IMAP ingestion; --dry-run flag
│   └── services/
│       ├── llm.py                 ← generate_quotation_draft(), classify_message(), _build_keyword_context()
│       └── tools/pricing.py       ← lookup_pricing tool; returns found: bool + results list
├── import_products.py             ← one-time; ProductList_updated.xlsx → database.Product (523 rows)
├── import_business_partners.py    ← one-time; Business Partner ALL.xlsx → database.Customer (6,414 rows)
├── docs/urls.md                   ← full URL reference for all apps
├── templates/                     ← all extend base.html
│   ├── base.html, dashboard.html, add_user.html, edit_user_role.html
│   ├── registration/              ← login, password reset
│   ├── database/                  ← product_list/add/edit, customer_list/detail/add/edit, broker_list/create
│   └── quotations/                ← lead_list/detail/create, quotation_list/detail/edit/pdf/select_lead,
│                                     market_order_list/create/detail, quotation_send_confirm
├── .claude/settings.json, commands/md-write.md
├── CLAUDE.md, manage.py, requirements.txt
```

Shell context: working directory is the project root. Use `python manage.py` not `python3 manage.py`.

---

## 17. App Structure

| App | Purpose |
|-----|---------|
| `aegis` | Auth & user management — CustomUser |
| `database` | Product, Customer, Broker — CRUD views |
| `quotations` | Module 2 — Lead, Quotation, QuotationLineItem, MarketOrder, LLM service |
| `ares`, `athena`, `hephaestus`, `hermes`, `themis` | Not yet created |

Future apps per module: `credit_risk`, `training`, `leads`.

---

## 18. External Services Status

| Service | Status | Notes |
|---------|--------|-------|
| together.ai | Active | `together==2.14.0`; `generate_quotation_draft` tested end-to-end |
| WhatsApp Business API | Pending Meta approval | Client must initiate — do NOT assume live |
| ConvoGenie | Client has account — reviewing | Integration scope TBD (see Section 9) |
| SAP | Deprioritised | Daily Excel replaces direct integration |
| Email (IMAP/SMTP) | Built — awaiting live credentials | Needs dummy Gmail App Password in `TeamEmailConfig` admin; delete post-demo |
| Hetzner VPS | Not provisioned | Pending hosting decision |
| Twilio/Deepgram/ElevenLabs | Not started | Only if Voice Stand-in greenlit |

---

## 19. Settings & Configuration

- `LOGIN_REDIRECT_URL = '/dashboard/'` · `LOGIN_URL = '/login/'` · `LOGOUT_REDIRECT_URL = '/login/'`
- Templates: `BASE_DIR / 'templates/'`
- Static files: whitenoise `CompressedManifestStaticFilesStorage`
- `DEBUG = False` in production — never deploy with DEBUG = True
- Secret key from environment variable only — never hardcoded

Environment variables (`.env` — never commit):
```
SECRET_KEY=  DEBUG=  DB_NAME=  DB_USER=  DB_PASSWORD=  DB_HOST=  DB_PORT=  TOGETHER_API_KEY=
```

---

## 20. Coding Conventions

- One Django app per major module
- Models: always `class Meta` with `verbose_name` and `verbose_name_plural`
- Views: CBVs for CRUD, FBVs for custom logic
- All LLM calls through `services/llm.py` — never call together.ai directly from views
- Tool definitions for function calling go in `services/tools/`
- Environment variables via `python-dotenv` + `os.environ` (NOT python-decouple)
- Requirements pinned: `pip freeze > requirements.txt` after each install

---

## 21. Non-Negotiables

- Never suggest running a local LLM or downloading model weights
- Never suggest Pinecone, Qdrant, Weaviate, Chroma — pgvector only
- Never commit secrets to version control
- Never deploy with DEBUG = True
- Never skip migration review before applying
- Never add a frontend JavaScript framework
- Never build Voice Stand-in until client greenlights a specific tier
- Never assume WhatsApp API is live — always check with Janav first
- Never quote Module 6 fee until ConvoGenie scope is resolved
