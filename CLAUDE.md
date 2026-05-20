# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

# FERITE-STEEL — Claude Code Project Context

This file is the single source of truth for all Claude tools (Claude Code, Cowork,
Claude.ai) on every aspect of the FERITE-STEEL project. Read it fully before doing
anything. Never deviate from the decisions recorded here without explicit instruction
from Janav.

**Last updated:** 20 May 2026 (session 9)

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

**Together.ai SDK installed** (`together==2.14.0`). `generate_quotation_draft` is fully wired.

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

**Phase 1: Complete. Phase 2: quotation UI/flow done; LLM draft generation wired; classify_message built; email send (SMTP) built; poll_emails command built. WhatsApp ingestion still pending Meta approval.**
**Current phase: Phase 2 — email ingestion pipeline complete (pending live credentials); WhatsApp ingestion deferred.**
**First deliverable: Quotation Automator (Module 2).**

### What is built
- Django project at `ferite_steel/` (macOS dev path: `/Users/janav/Programs/ferite_steel/`)
- PostgreSQL 16 database `ferite_steel_db` connected
- `CustomUser` model in `aegis` app with `team` field (`team_9`/`cs`/`market`/`corporate`) and role choices (`admin`/`lead`/`member`/`primary`/`rolling`/`loading_dock`)
- Full auth flow: login, logout, register (pending admin approval), password reset
- User management: add user, directory, edit role, approve, delete — all admin-gated; forms include team dropdown with **JavaScript role filter** (role options update dynamically based on selected team)
- `base.html` built — all templates extend it; nav gated by `request.user.role`; Database dropdown in nav (Customers, Products, Brokers for market/admin)
- Dashboard with lead/quotation stats, scoped by role (admin/lead see all; member sees own); + New Lead / + New Quotation / + Market Order buttons (Market Order button visible to market team + admin only)
- `database` app: `Product`, `Customer`, `Broker` models (moved from quotations in session 4)
- `quotations` app: `Lead`, `Quotation`, `QuotationLineItem`, `MarketOrder` models; references `database.Broker` and `database.Customer` via FK strings
- Lead: company, industry, location, broker (optional FK) fields; list/create/detail/delete views; delete button on list and detail (with cascade warning modal on detail)
- Quotation: full edit flow with inline formset (line items), JS auto-calculation (amount = rate × tons), WeasyPrint PDF
- Quotation versioning: Revise creates v2/v3 etc. cloned from current; all versions share a root's outcome
- **Customer model** (expanded session 8): `customer_code`, `billing_address`, `shipping_address`, `gst_number`, `payment_terms` (advance/cash), `competitors` (TextField, one per line), `rm` (FK to CustomUser, nullable) added; `location` removed. Auto-upserted whenever a quotation is saved. `handling_team` field retained.
- Customer list + detail views with team scope; customer edit view; list columns: Code, Name, Company, Phone, GST No., Payment Terms, Handling Team
- Outcome (Win/Loss/Not Updated): shown on quotation detail as quick-select buttons; stored only on root quotation; shared across all versions
- Broker-sourced quotations: Send button visible but sends text-only rate email (no PDF); PDF header reads "INTERNAL — RATES ONLY"
- Send button: links to `quotation_send` compose/confirm view; sends via SMTP using `TeamEmailConfig`; PDF attached for non-broker leads; broker leads get text-only rate email
- Approve flow: lead and admin roles only
- LLM service at `quotations/services/llm.py` — `generate_quotation_draft(lead, entity_notes)` fully implemented; builds system prompt, calls together.ai with tool-use loop, executes `lookup_pricing` tool calls, parses JSON response; system prompt instructs LLM to ignore rates in enquiry text and focus only on the newest part of reply chains; UOM context (ton/kg, 1T=1000KG) included; `quotation_create` calls it with graceful fallback to blank editor
- `ferite_steel/ai.py` — shared Together client (`together_client`) used by all service layers; initialized once at import time from `TOGETHER_API_KEY` env var
- `lookup_pricing` tool at `quotations/services/tools/pricing.py` — queries `database.Product` by size/hsn_code/sub_type; returns `found: bool` + results list (result dicts include `make`, `godown`, `pieces` keys — bug fix session 9: was incorrectly referencing `p.location` instead of `p.godown`, causing silent AttributeError on every LLM draft generation)
- Broker model: list + create views at `/database/brokers/`; registered in database admin
- MarketOrder model: full broker order flow — `new` → `rate_sent` → `broker_confirmed` → `do_pending` → `completed`; views + templates at `/quotations/market-orders/`
- **Product catalog** (session 4, updated session 7): `Product` model with `make` (Main/Rolling/Plate), `sub_type` (Angle/Channel/UB/UC/Beam/Flat/Red Material/TMT), `size`, `length` (CharField), `grade`, `godown`, `site` (Site 1/Site 2), `quantity`, `rate`, `pieces`. Product list is a **grouped view**: rows grouped by sub_type + size; cascading dropdowns — Make → Length → Grade → Site — resolve to the specific variant; rate/qty/HSN/godown update live. No make tabs or sub-type filter; just a text search box. Product catalog JSON endpoint at `/database/products/catalog.json`. Add/edit forms include Godown + Site fields.
- **Quotation line item picker** (session 7, updated sessions 8–9): each line item row has a "⌕ pick" button opening a modal with the full grouped catalog. Picker uses an **accordion layout** — clicking a group header expands its variants, collapses others. Selecting a variant auto-fills product_name, make, length, hsn_code, sets the `product` FK (hidden field), and sets the **purchase rate** input. `make` and `length` fields are `readonly` in the form (filled by picker only, not user-editable). `pcs` field is readonly+greyed when the selected product has no pieces defined.
- **Quotation line item UOM** (session 8): `uom` field (ton/kg) on `QuotationLineItem`. Dropdown in edit table. Server-side: `total_price = (quantity / 1000) * unit_price` if `uom == 'kg'`, else `quantity * unit_price`. LLM draft respects UOM as stated by customer.
- **Pricing breakdown** (session 9, redesigned from session 8): each line item row has a companion collapsible add-on row (toggled by "⊞ add-ons" button) with 7 per-row inputs: Parity, Cutting, Loading, Transport, Margin, Interest, Commission — client-side only, not model fields. JS sums them into `unit_price` (readonly final sell rate, stored in DB). Customer never sees add-ons — only the final sell rate appears on PDF. Add-on defaults pre-filled from `customer.notes` (`--- Pricing Add-ons ---` section) read-only at page load. Add-ons are **not written back** to customer notes on save (per-session only). `_parse_addon_notes()` helper in `quotations/views.py` reads defaults; `_update_addon_notes()` removed (dead code after session 9 redesign).
- **Customer notes pre-fill in line items** (session 9): `customer.notes` content is injected into the `notes` field of each line item row as a pre-fill default. Editable per line item.
- **Win outcome tracking** (session 9): when outcome = Win, the quotation detail shows which specific version won ("Won Via: QT-00001-v2" with a link). `winning_quotation` FK on the root Quotation records this. `stock_deducted` BooleanField guards against double-deduction — stock is only deducted once even if Win is clicked again.
- **Stock deduction on Win** (session 9): `_deduct_stock(quotation)` called once when outcome first set to Win. For each line item with a `product` FK set: deducts `quantity` (converted to tons if uom=kg) from `Product.quantity` using `Greatest(F('quantity') - qty, Decimal('0'))` — atomic DB update, never goes negative. LLM-generated line items without a `product` FK are skipped (no stock deduction — salesperson must re-pick from catalog to link the FK).
- `import_products.py` at project root — one-time script; imported 523 products from `ProductList_updated.xlsx`; auto-generated HSN codes `IMP-0001…`; rates all 0 (column was blank in Excel — fill via admin)
- Django admin themed with `django-jazzmin`; Product, Customer, Broker, MarketOrder, **ProductKeyword, TeamEmailConfig** registered
- Static files served via `whitenoise`
- WeasyPrint installed (`pip install weasyprint` + `brew install pango` on macOS)
- **`ProductKeyword` model** (session 6): maps client trade terms (e.g. "sariya") to canonical product names; admin-editable; `_build_keyword_context()` fetches active keywords and injects them into the LLM system prompt on every `generate_quotation_draft` call
- **`TeamEmailConfig` model** (session 6): IMAP credentials per team for email ingestion; unique per team; admin-only management; password field has help text to use an App Password
- **`classify_message(text)`** (session 6): LLM classifier — returns True if text is a product inquiry; called before creating any Lead from inbound messages; uses a YES/NO single-word response from together.ai
- **`poll_emails` management command** (session 6, improved session 8): full IMAP ingestion — connects to each active TeamEmailConfig inbox, fetches UNSEEN messages, pre-filters spam senders, calls `classify_message`, creates Leads for genuine inquiries, marks emails as Seen. `--dry-run` flag for testing without side effects. `_strip_reply_chain()` handles Gmail reply chains (On ... wrote:), Outlook reply blocks (From: + Sent: with optional blank line between them), `-----Original Message-----`, and nested `--------- Forwarded message ---------` (cut only after real content seen — outer forward wrapper is preserved).
- **Email send flow** (session 6): `quotation_send` view now shows a compose/confirm form (`quotation_send_confirm.html`) pre-filled with subject and body. On submit: looks up active `TeamEmailConfig` for the lead's team, generates PDF via WeasyPrint (non-broker only), sends via SMTP (host derived by replacing "imap." with "smtp."). Broker quotations get a text-only rate email (no PDF). Falls back to "marked as sent" if no active config exists.
- **Quotation list** (session 8): "All Quotations" and "All Leads" nav links at top of quotation list page.
- Quotation edit header shows customer name and company for context.

### What is NOT yet built (planned for next session)
- Email ingestion live test — `poll_emails` is built; needs a dummy Gmail account added to `TeamEmailConfig` in admin with a valid App Password (Janav to provide credentials); to be deleted post-demo
- WhatsApp ingestion — deferred until Meta Business API approval confirmed
- Customer handover view (`customer_handover`) — lead/admin only; `handling_team` field exists, view not yet built
- Product rates — all 0 after import (Excel rate column was blank); must be filled via admin
- TMT products missing from catalog — were not present in imported Excel; must be added manually or via a second import

### Pending before Phase 2 is fully live
- WhatsApp Business API Meta approval (do not build until confirmed)
- Dummy Gmail credentials added to `TeamEmailConfig` for email ingestion demo
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
  `together==2.14.0` (LLM API client — wired in `ferite_steel/ai.py`)

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

### Product (database.models.Product)
Master product catalog. 523 rows imported from client Excel (rates all 0 — fill via admin).
- `hsn_code` — CharField `blank=True` (no longer unique; auto-generated `IMP-0001…` during import; update with real HSN codes when available)
- `make` — CharField choices: `main`, `rolling`, `plate` (was `type` before session 7)
- `sub_type` — CharField choices: `angle`, `channel`, `ub`, `uc`, `beam`, `flat`, `red_material`, `tmt`; blank=True. Valid sub-types per make enforced via JS in add/edit forms and `SUB_TYPE_MAP` class attribute
- `size` — CharField
- `length` — CharField blank (free text, e.g. "12 mtr", "8-11 mtr")
- `grade` — CharField blank
- `godown` — CharField blank (free text warehouse/plot location, e.g. "Plot 557"; was `location` before session 7)
- `site` — CharField choices: `site_1` (Site 1), `site_2` (Site 2); blank=True
- `pieces` — IntegerField null/blank
- `quantity` — DecimalField (T)
- `rate` — DecimalField (₹/T)
- `is_active` — BooleanField (default True)
- `last_updated` — auto_now DateTimeField
Views: product_list (grouped view + text search), product_add, product_edit, product_delete, product_catalog_json. All at `/database/products/`.
`_build_product_groups(products)` helper in `database/views.py` — groups a queryset into nested dict: sub_type+size → make → length → grade → site → {id, rate, qty, hsn, godown, site_display, pieces}. Used by both product_list and product_catalog_json. `pieces` is included so the quotation picker can set the PCS field readonly when a product has no pieces defined.

### Customer (database.models.Customer)
Stores remembered transport costs and commercial details per customer, matched by name + company (case-insensitive).
- `customer_code` — CharField unique, null/blank (client assigns codes; pre-filled when client provides their DB)
- `name`, `company`, `phone`, `email` — CharFields
- `billing_address`, `shipping_address` — TextFields blank (replaced old `location` field)
- `gst_number` — CharField blank
- `payment_terms` — CharField choices: `advance`/`cash`, blank
- `transport_extra` — DecimalField (default 0)
- `loading_rate` — DecimalField (default 0.5 — ₹/ton)
- `notes` — TextField blank (AI context + `--- Pricing Add-ons ---` section; add-on defaults read from here at quotation edit page load; not written back on save since session 9)
- `competitors` — TextField blank (one competitor per line; display only)
- `rm` — FK to `settings.AUTH_USER_MODEL` (relationship manager; nullable, SET_NULL)
- `handling_team` — CharField choices: TEAM_CHOICES, nullable/blank
- `updated_at` — auto_now DateTimeField
Auto-upserted whenever a quotation is saved. Views at `/database/customers/`. List columns: Code, Name, Company, Phone, GST No., Payment Terms, Handling Team.

### Broker (database.models.Broker)
Stores broker information for the Market team. Separate from Customer (different flow direction, no transport cost memory).
- `name`, `company`, `location`, `phone`, `email` — CharFields
- `notes` — TextField blank (AI context: usual margins, preferred products, etc.)
- `is_active` — BooleanField (default True)
- `created_at` — auto_now_add DateTimeField
Views at `/database/brokers/`.

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
- `winning_quotation` — self-FK (nullable, SET_NULL, related_name `won_as`); set when outcome = win; records which specific version won
- `stock_deducted` — BooleanField (default False); set True after `_deduct_stock()` runs; guards idempotency (stock only deducted once per root quotation)
- `llm_raw_response` — TextField (stores raw JSON from LLM draft generation)
- `payment_terms` — CharField choices: `Advance`, `Cash`; default `Advance`
- `delivery_address` — CharField
- `transport_extra`, `sgst_percent`, `cgst_percent` — DecimalFields
- `total_amount`, `notes`, `valid_until`
- `created_by`, `approved_by`, `created_at`, `approved_at`, `sent_at`

Broker-sourced quotations (where `lead.broker` is not null) are internal-only: Send button hidden, PDF header reads "INTERNAL — RATES ONLY".

### QuotationLineItem (quotations.models.QuotationLineItem)
- `quotation` — FK to Quotation
- `product` — FK to `database.Product` (nullable, SET_NULL, related_name `line_items`); set by the picker; NULL for LLM-generated items (LLM fills text fields only)
- `product_name`, `make` — CharFields; `make` is readonly in form (filled by picker)
- `length` — CharField blank; readonly in form (filled by picker)
- `pcs` — IntegerField nullable; readonly+greyed in form when selected product has no pieces defined
- `uom` — CharField choices: `ton`/`kg`, default `ton`
- `quantity` — DecimalField decimal_places=3 (ton or kg as per uom)
- `unit_price` — DecimalField (final sell rate; readonly in form; JS-calculated from purchase_rate + 7 per-row add-ons)
- `total_price` — DecimalField (server-side: `(quantity/1000)*unit_price` if kg, else `quantity*unit_price`)
- `notes` — TextField blank (pre-filled from `customer.notes` content; editable per line item)
`make`, `length`, and `uom` rendered as columns in quotation edit table. The "⌕ pick" button fills product FK + purchase-rate input (client-side only); JS then recalcs `unit_price` from purchase_rate + per-row add-ons.

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

### ProductKeyword (quotations.models.ProductKeyword)
Maps company-specific client terms to canonical product names for LLM prompt injection.
- `keyword` — CharField (what clients say, e.g. "sariya", "angle", "12mm")
- `maps_to` — CharField (product name or code, e.g. "TMT Bars 12mm")
- `notes` — CharField blank (e.g. "Hindi term for TMT bars")
- `is_active` — BooleanField (default True)
Admin-editable (`list_editable` on `is_active`). Active keywords fetched by `_build_keyword_context()` and injected into the LLM system prompt on every `generate_quotation_draft` call.

### TeamEmailConfig (quotations.models.TeamEmailConfig)
IMAP credentials for team shared email accounts, used by `poll_emails` management command.
- `team` — CharField choices: TEAM_CHOICES (unique per team)
- `email_address` — EmailField (shared team inbox)
- `imap_host` — CharField (default `imap.gmail.com`)
- `imap_username`, `imap_password` — CharFields; use an App Password, not account password
- `imap_port` — IntegerField (default 993)
- `use_ssl` — BooleanField (default True)
- `is_active` — BooleanField (default True)
Admin-only management (`list_editable` on `is_active`). SMTP host derived at send time by replacing "imap." with "smtp." in `imap_host`.

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

### Product rates
1. All 523 imported product rates are 0 — the RATE column in the Excel was blank. Ask client to either provide a rate file or fill them in via admin.

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
- **Product rates:** All 523 imported products have rate=0. Client must provide rates.
- **TMT products missing:** Not present in imported catalog — must be added manually or via re-import.
- **Email dummy account:** Dummy Gmail credentials to be added to `TeamEmailConfig` in admin for demo. Janav to provide App Password — do not hardcode. Delete the account post-demo.

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
13. **Shared AI client:** `ferite_steel/ai.py` holds the single `together_client` instance. All service layers import from there — never instantiate `Together(...)` directly in a service or view. If a new app needs LLM access, import from `ferite_steel.ai`, don't create a new client.
14. **Win tracks the specific version, not just the lead:** `winning_quotation` FK is set to the exact `Quotation` instance the user marks as won — not the root. This is intentional: a lead may have 3 revisions; the salesperson picks which one closed the deal.
15. **Stock deduction is one-time and irreversible per deal:** `stock_deducted` guards against repeat deduction. Changing outcome away from Win and back again does NOT re-deduct. Stock is never restored on outcome change (Loss/Not Updated after Win). This is intentional — physical stock has already moved.
16. **Per-row pricing add-ons are session-only:** The 7 add-on inputs (Parity, Cutting, Loading, Transport, Margin, Interest, Commission) live only in the browser. Defaults are read from `customer.notes` on page load; values are NOT written back on save. They are never stored in any model field. Only the resulting `unit_price` is persisted.
17. **Product FK on QuotationLineItem is set only via the picker:** The LLM fills product_name as free text and never sets the `product` FK. Stock deduction skips any line item without a `product_id`. The salesperson must re-pick from catalog after LLM draft generation to link the FK and enable stock tracking.

---

## 16. Project Root & Directory Structure

```
ferite_steel/                      ← project root
│
├── ferite_steel/                  ← Django project config
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── ai.py                      ← shared Together client (together_client); imported by all LLM service layers
│
├── aegis/                         ← auth & user management
│   ├── models.py                  ← CustomUser (team + role fields)
│   ├── views.py                   ← dashboard, add_user, directory, edit_role, register, approve, delete
│   ├── forms.py                   ← AddUserForm, EditRoleForm (both include team field)
│   └── urls.py
│
├── database/                      ← shared entity models (session 4)
│   ├── models.py                  ← Product, Customer, Broker
│   ├── views.py                   ← product_list/add/edit/delete, customer_list/detail/add/edit, broker_list/create
│   ├── forms.py                   ← ProductForm, CustomerForm, BrokerForm
│   ├── admin.py                   ← Product, Customer, Broker registered
│   ├── urls.py                    ← /database/ prefix
│   └── migrations/                ← 0001–0011
│
├── quotations/                    ← Module 2
│   ├── models.py                  ← Lead, Quotation, QuotationLineItem, MarketOrder,
│   │                                 ProductKeyword, TeamEmailConfig
│   ├── views.py                   ← all quotation, lead, and market order views
│   │                                 + customer_handover (planned)
│   ├── forms.py                   ← ManualLeadForm, QuotationEditForm, LineItemFormSet,
│   │                                 MarketOrderForm, MarketOrderRateForm,
│   │                                 MarketOrderAssignForm, MarketOrderDOForm
│   ├── admin.py                   ← MarketOrder, Lead, Quotation, ProductKeyword, TeamEmailConfig registered
│   ├── urls.py
│   ├── management/
│   │   └── commands/
│   │       └── poll_emails.py     ← IMAP ingestion: spam pre-filter → classify_message → create Lead; --dry-run flag
│   └── services/
│       ├── llm.py                 ← generate_quotation_draft(lead, entity_notes) — LIVE; tool-use loop with lookup_pricing; keyword injection
│       │                             classify_message(text) — LIVE; YES/NO LLM classifier for inbound messages
│       │                             _build_keyword_context() — fetches active ProductKeywords; injects into system prompt
│       └── tools/
│           └── pricing.py         ← lookup_pricing tool — queries database.Product; returns found: bool + results
│
├── import_products.py             ← one-time script; imports ProductList_updated.xlsx → database.Product
│
├── templates/                     ← global templates (all extend base.html)
│   ├── base.html                  ← nav gated by role; Database dropdown (Customers/Products/Brokers)
│   ├── dashboard.html             ← + New Lead / + New Quotation / + Market Order buttons
│   ├── add_user.html              ← includes JS team→role filter
│   ├── edit_user_role.html        ← includes JS team→role filter
│   ├── registration/              ← login, password reset
│   ├── database/
│   │   ├── product_list.html      ← grouped view; cascading dropdowns (Make→Length→Grade→Site); text search only
│   │   ├── product_add.html       ← JS sub-type filter by make; Plate hides sub-type field; Godown + Site fields
│   │   ├── product_edit.html      ← same JS; pre-selects current sub_type; Godown + Site fields
│   │   ├── customer_list.html     ← team-scoped
│   │   ├── customer_detail.html   ← lead history
│   │   ├── customer_add.html
│   │   ├── customer_edit.html
│   │   ├── broker_list.html
│   │   └── broker_create.html
│   └── quotations/
│       ├── lead_list.html
│       ├── lead_detail.html
│       ├── lead_create.html
│       ├── quotation_list.html    ← Outcome column (Win/Loss/—)
│       ├── quotation_detail.html  ← Revise, Send/Internal Copy, Edit, PDF, Outcome, Versions; "Won Via" + "Stock Deducted" badge shown when outcome=win
│       ├── quotation_edit.html    ← inline formset + JS auto-calc; per-row "⊞ add-ons" collapsible sub-row (7 add-on inputs); "⌕ pick" button per row; accordion product picker modal; customer notes pre-fill in line item notes
│       ├── quotation_pdf.html     ← WeasyPrint A4; "INTERNAL — RATES ONLY" header for broker quotations
│       ├── quotation_select_lead.html
│       ├── market_order_list.html
│       ├── market_order_create.html
│       ├── market_order_detail.html  ← 4-step flow: rate → confirm → assign DO → DO number
│       └── quotation_send_confirm.html  ← email compose form; pre-filled subject/body; PDF note hidden for broker leads
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
| `/quotations/market-orders/`                  | market_order_list            |
| `/quotations/market-orders/create/`           | market_order_create          |
| `/quotations/market-orders/<pk>/`             | market_order_detail          |
| `/quotations/market-orders/<pk>/set-rate/`    | market_order_set_rate        |
| `/quotations/market-orders/<pk>/confirm/`     | market_order_confirm         |
| `/quotations/market-orders/<pk>/assign-do/`   | market_order_assign_do       |
| `/quotations/market-orders/<pk>/set-do/`      | market_order_set_do          |

**database** (prefix: `/database/`):

| URL                                           | View / Name       |
|-----------------------------------------------|-------------------|
| `/database/products/`                         | product_list      |
| `/database/products/add/`                     | product_add            |
| `/database/products/catalog.json`             | product_catalog_json   |
| `/database/products/<pk>/edit/`               | product_edit           |
| `/database/products/<pk>/delete/`             | product_delete         |
| `/database/customers/`                        | customer_list     |
| `/database/customers/add/`                    | customer_add      |
| `/database/customers/<pk>/`                   | customer_detail   |
| `/database/customers/<pk>/edit/`              | customer_edit     |
| `/database/brokers/`                          | broker_list       |
| `/database/brokers/add/`                      | broker_create     |

**admin**: `/admin/` — jazzmin-themed Django admin.

---

## 18. App Structure

| App          | Purpose                                                                        |
|--------------|--------------------------------------------------------------------------------|
| `aegis`      | Auth & user management — CustomUser                                            |
| `database`   | Shared entity models — Product, Customer, Broker; CRUD views                  |
| `quotations` | Module 2 — Lead, Quotation, QuotationLineItem, MarketOrder, LLM service       |
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
| together.ai           | Active — API key set, SDK wired | `together==2.14.0` installed; `generate_quotation_draft` tested end-to-end |
| WhatsApp Business API | Pending Meta approval           | Client must initiate — do NOT assume live     |
| ConvoGenie            | Client has account — reviewing  | Integration scope TBD (see Section 9)        |
| SAP                   | Deprioritised                   | Daily Excel replaces direct integration      |
| Email (IMAP/SMTP)     | Built — awaiting live credentials | `poll_emails` command + SMTP send built; dummy Gmail credentials needed in `TeamEmailConfig` admin; delete post-demo |
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
