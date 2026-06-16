# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

# FERITE-STEEL — Claude Code Project Context

This file is the single source of truth for all Claude tools (Claude Code, Cowork,
Claude.ai) on every aspect of the FERITE-STEEL project. Read it fully before doing
anything. Never deviate from the decisions recorded here without explicit instruction
from Janav.

**Last updated:** 16 Jun 2026 (session 22 — DNS cutover complete, email pipeline live, SMTP tested, lead list/detail received-via display, Jazzmin back-to-CRM link)

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

**Phase 1 complete. Phase 2 (Quotation Automator): complete — email pipeline is LIVE. Phase 3 (Training + Case Solver): ALL sub-modules complete and tested — 3A (Case Management), 3B (Quiz System), 3C (RAG Q&A pipeline) all working end-to-end.**
**Current work: Session 22 complete — DNS cutover done (crm.ferrite.in → Hetzner), email pipeline live (polling sales@ferrite.in + fcc@ferrite.in, classifying real inquiries, creating leads + notifications), SMTP tested. Next: delete GCP VM, then Phase 4 (Credit Risk AI) when client is ready.**

### What is built

**Auth & Users:** Full auth flow (login/logout/register/password reset). CustomUser with `team` + `role`. User management (add/edit/approve/delete) admin-gated. JS role filter in add/edit user forms. Nav gated by role; Database dropdown (Customers/Products/Brokers for market/admin). Dashboard stats scoped by role (admin/lead see all; member sees own). Market Order button visible to market + admin only.

**Product catalog:** 2,117 rows total (523 from ProductList_updated.xlsx + 1,594 from Borker list & Item list.xlsx via `import_broker_items.py`). Rates all 0 — fill via admin. Grouped view — rows by sub_type+size; cascading dropdowns Make→Length→Grade→Site; text search only. Relational pricing: `base_product` self-FK + `rate_offset`; `effective_rate` = base rate + offset (or own rate). No chaining — derived products always point directly to a base. `_build_product_groups()` used by product list + catalog JSON at `/database/products/catalog.json`.

**Customer & Broker:** Customer list team-scoped. 6,414 SAP records imported (`import_business_partners.py`); upsert key = `customer_code`. Customer auto-upserted on every quotation save. Broker CRUD at `/database/brokers/`. 483 brokers imported from `extra_data/Borker list & Item list.xlsx` via `import_broker_items.py`; upsert key = `name`.

**Lead flow:** List/create/detail/delete with cascade warning modal. Fields: company, industry, location, broker FK (optional; set for market team leads).

**Quotation flow:** Edit form with inline formset + JS auto-calc. WeasyPrint PDF. Versioning — Revise creates v2/v3 cloned from current. Outcome (Win/Loss/Not Updated) stored on root, shared across versions. Win records exact winning version via `winning_quotation` FK. Stock deduction on first Win only — one-time, irreversible (`stock_deducted` guard). Approve: lead + admin only. Broker-sourced quotations (`lead.broker ≠ null`): PDF = "INTERNAL — RATES ONLY"; text-only rate email.

**Quotation line item picker:** "⌕ pick" button → accordion modal with full grouped catalog. Fills product FK, make, length, HSN, purchase rate. `make` + `length` readonly (picker only). `pcs` readonly+greyed when product has no pieces.

**Pricing add-ons:** 7 per-row collapsible inputs (Parity/Cutting/Loading/Transport/Margin/Interest/Commission) under "⊞ add-ons". Session-only — defaults read from `customer.notes` (`--- Pricing Add-ons ---` section) at page load; NOT written back on save. Only `unit_price` persisted. UOM (ton/kg) per line item. `discount_pct` per line item; `final_price` = `total_price × (1 − pct/100)` — used for discount-aware taxes/grand total. `floatformat:2` applied globally.

**Stock deduction on Win:** `_deduct_stock()` called once via `stock_deducted` guard. Deducts quantity (converted to tons if uom=kg) using `Greatest(F('quantity') - qty, 0)` — atomic, never negative. Skips line items without `product` FK (LLM-generated items).

**LLM / AI:** `generate_quotation_draft(lead, entity_notes)` in `quotations/services/llm.py` — tool-use loop with `lookup_pricing`, ProductKeyword injection, UOM context, reply-chain focus in system prompt. Graceful fallback to blank editor. `classify_message(text)` — YES/NO classifier for inbound messages. `classify_broker_response(text)` — returns `'confirmation'`/`'counter'`/`'other'` for broker replies. Shared `together_client` in `ferite_steel/ai.py`.

**Email pipeline:** `poll_emails` management command — IMAP per TeamEmailConfig, spam pre-filter, broker reply detection (`_find_broker`), classify_message, Lead + MarketOrder creation for broker senders, marks Seen. `--dry-run` flag. `--scheduled` flag throttles by `TeamEmailConfig.poll_interval_minutes`; stamps `last_polled_at` after each real run. "Poll Inbox" button on lead list (admin/lead only) hits `poll_emails_now` view. Cron: `* * * * * manage.py poll_emails --scheduled` (running on www-data crontab; logs to `/var/log/poll_emails.log` — must be owned by www-data). `_strip_reply_chain()` handles Gmail/Outlook/forwarded formats. `quotation_send` — compose/confirm form, SMTP send, PDF attach (non-broker), text-only rate email for broker leads. SMTP uses dedicated `smtp_host`/`smtp_username`/`smtp_password` fields on `TeamEmailConfig` (falls back to imap equivalents if blank). **LIVE: polling sales@ferrite.in + fcc@ferrite.in; poll intervals set to prime numbers (2, 3, 5, 7, 11 min) to avoid simultaneous polls.**

**Broker-to-DO pipeline:** `_find_broker(email_addr)` matches inbound sender to active Broker. Broker email → Lead (with broker FK) + MarketOrder auto-created. Broker reply → `classify_broker_response()` → if confirmation: MarketOrder status → `broker_confirmed`, `broker_confirmed_at` stamped; if counter: reply appended to Lead notes. `notify_loading_dock` signal on `MarketOrder` post_save — fires only when `status` field transitions to `broker_confirmed`, emails `loading_dock_member`. DO send: `market_order_do_send` view + template — user enters DO number, gets compose/confirm UI, sends text to broker email. MarketOrder status → `completed` on send. `lead` FK added to `MarketOrder`.

**Market team:** MarketOrder full flow (`new`→`rate_sent`→`broker_confirmed`→`do_pending`→`completed`). Visual pipeline timeline on detail page (numbered nodes, connector line, state-aware colours). Separate from Quotation — tracks logistics, not pricing.

### What is built (continued from above)

**Lead case notes + voice dictation:** `lead_notes_raw` + `lead_notes_clean` fields on `Lead` (migration 0025). Case Notes card on lead detail — raw textarea with 🎤 Dictate button (Web Speech API, `en-IN`, continuous mode), Save + AI Cleanup buttons, cleaned notes textarea with Save + "Convert to Case" button. `cleanup_lead_notes(raw)` in `quotations/services/llm.py`. `lead_save_notes` view handles `save`/`cleanup`/`save_clean` actions. Voice dictation post-processes final results: punctuation word substitution + ProductKeyword trade-term substitution (longest-first). Chrome/Edge only.

**Training app (Sub-module 3A — Case Management):** `training` app with `Case` model (title, problem_description, context, resolution, departments JSONField, customer FK nullable, created_by FK, created_at). Views: `training_home` (bento grid — 3A live, 3B live, 3C placeholder), `case_list`, `case_detail`, `case_create`, `case_edit`, `case_delete`. URLs at `/training/`. Training sidebar link live (gated by `view_case` perm). "Convert to Case" button on lead detail wired — passes `notes` + `lead` as query params to `case_create`. Permissions: `view_case` in BASE (all roles), `add/change/delete_case` in LEAD_EXTRA (lead + admin).

**Training app (Sub-module 3B — Quiz System):** `QuizSet` (title, description, departments JSONField, created_by, created_at), `Question` (question_text, correct_answer, source, quiz_set FK nullable, departments JSONField, created_by, created_at), `QuizAttempt` (user, quiz_set, score, total_questions, passed, completed_at). Views: `quiz_list`, `quiz_detail`, `quiz_take`, `quiz_results`, `quiz_set_create`, `quiz_set_edit`, `quiz_set_delete`, `question_create`, `question_create_for_quiz`, `question_edit`, `question_delete`. `judge_quiz_answer(question, correct_answer, user_answer)` in `training/services/llm.py` — calls together.ai to judge correctness and explain if wrong. Pass threshold: 70%. Best attempt tracked per user per quiz set. Department filtering: users only see quiz sets matching their team. **Quiz/question CRUD restricted to admin only** (QUIZ_MANAGE permission block in `aegis/signals.py`; auto-assigned to admin role only).

**Notification system:** `Notification` model in `aegis/models.py` (user FK, title, message, link, type choices, is_read, created_at). `notify(users, title, message, link, notif_type)` utility in `aegis/notifications.py` — bulk_creates. Context processor `aegis.context_processors.notification_count` injects `unread_notification_count` globally. Dashboard shows notifications panel (right column, up to 12, scrollable, per-type icons, unread highlighting, mark-all-read). Full notifications page at `/notifications/`. Wired at: lead_create, quotation_approve, quotation_outcome (win/loss), market_order_confirm, market_order_assign_do, market_order_set_do, case_create, poll_emails (new inquiry lead → team + admins; broker confirmation → market + admins; broker counter → market + admins).

**Team chat:** `chat` app with `ChatMessage` model (channel, sender FK, content, created_at). Channels: all_staff + user's own team; admins see all. Views: `chat_home` (renders last 100 messages), `chat_send` (POST → JSON), `chat_poll` (GET ?channel=&since=id → JSON). 4-second JS polling, tracks `lastId`, sanitizes with `escHtml()`. Auto-resize textarea, Enter to send, Shift+Enter for newline. At `/chat/`.

**Frontend redesign (session 15):** All pages redesigned with DM Sans font, blue accent (`#2563EB`), CSS variable theming. Multi-panel pages use bento/card grid layouts. Table pages use dark headers, `.9rem` font, click-to-navigate rows. Role chips (admin=blue, lead=green, member=grey), dept-tag chips (team_9=blue, cs=green, market=orange, corporate=purple), status pills per entity type. Pages redesigned: directory, profile, case_list, case_detail, case_create, case_edit, case_confirm_delete, quiz_list, quiz_take, broker_list, broker_create, market_order_list, market_order_create, quotation_select_lead, quotation_send_confirm, add_user, edit_user_role, dashboard.

**Customer notes surfaced across views:** `_quotation_context` passes `customer_notes_display` (raw notes stripped of `--- Pricing Add-ons ---` section) — shown as a read-only card on quotation detail. `lead_detail` view also fetches and passes `customer_notes_display` — shown as a card above the Quotations section. Quotation editor (`quotation_edit`) shows `customer_notes` (raw, unstripped — also used by JS for add-on defaults) as a visible card between Cost Summary and Save.

**Quotation notes:** `quotation_notes_raw` + `quotation_notes_clean` fields on `Quotation` (migration 0028). Quotation Notes card on quotation detail page — raw textarea with 🎤 Dictate button (same Web Speech API engine as lead notes — punctuation substitution + ProductKeyword substitution, `en-IN`, continuous), Save + AI Cleanup buttons; cleaned notes section (conditional) with Save + "Convert to Case" button. `quotation_save_notes` view at `/<pk>/notes/` handles `save`/`cleanup`/`save_clean` actions using `cleanup_lead_notes()` from `quotations/services/llm.py`. `_quotation_context` now includes `voice_keywords` for the dictation JS.

**Guide app:** `guide` Django app at `/guide/`. Three pages: `guide_core` (`/guide/core/`), `guide_quotations` (`/guide/quotations/`), `guide_training` (`/guide/training/`). "Codex" theme — deep forest green sidebar (`#071910`, active `#34D399`), warm sage page background (`#EAF0E4`), Cormorant Garamond serif section titles. Shared `templates/guide/_sb_guide.html` overrides `--sb-*` and `--accent`/`--accent-h` variables. Editorial bottom-border tab nav. Role-gated sections: admin-only User Management on core, market-team Market Orders on quotations, admin-only Managing Content on training. "User Guide" link added to sidebar under Tools.

**Permission cache fix:** `aegis/signals.py` `post_save` signal now clears `_perm_cache` and `_user_perm_cache` on the instance after `user_permissions.set(...)` — prevents stale cached permissions in the same request after a role change.

**Training app (Sub-module 3C — RAG Q&A):** `KnowledgeDocument` + `DocumentChunk` models (migration 0005). Services in `training/services/`: `extractor.py` (pypdf/python-docx → text), `embedder.py` (together.ai `togethercomputer/m2-bert-80M-8k-retrieval` → 1024-dim vectors), `onedrive.py` (MSAL upload to OneDrive — needs live credentials), `processor.py` (orchestrates extract → chunk → embed → upload). Views: `document_list`, `document_create`, `document_detail`, `document_delete`, `document_ask` (RAG Q&A — semantic search over chunks + LLM answer via together.ai). Templates: full CRUD + Q&A UI at `/training/documents/`. **End-to-end test pending** — comment out OneDrive lines in `processor.py` (line 5 import, lines 11–12 upload call) before local testing.

**Training UI (session 18):** All 21 training templates redesigned with warm amber/cream theme. `templates/training/_sb_amber.html` — shared include that overrides all `--sb-*` CSS variables to amber; included at top of `extra_head` in every training template. Non-training pages retain default navy sidebar from `base.html` `:root`. `base.html` refactored with 15 `--sb-*` sub-tokens so sidebar colour is fully CSS-variable-driven per page.

**Docs:** `docs/module3_plan.md`, `docs/module3_plan.docx` (professional Word doc with diagrams), `docs/user_manual_quotation_automator.md`, `docs/developer_manual.md` all created session 14.

### What is NOT yet built (planned for next sessions)
- WhatsApp ingestion — deferred until Meta approval confirmed
- Product rates — all 0 after import; must be filled via admin
- TMT products missing — must be added manually or re-imported
- **Existing role checks in views** — gradually replace `request.user.role == 'x'` with `request.user.has_perm()` as views are touched (Architecture Decision 18)
- OneDrive integration for 3C — needs live MSAL credentials (`AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`, `ONEDRIVE_FOLDER`) in `.env`; lines already commented out in `processor.py`
- GCP e2-small VM — DNS cutover done; VM still running, delete when confirmed stable on Hetzner

### Pending before Phase 2 is fully live
- WhatsApp Business API Meta approval (email pipeline already live)

---

## 4. Tech Stack

### Backend
- **Framework:** Django 6.0.3 · **Python:** 3.12 · **Database:** PostgreSQL 16 (`ferite_steel_db`)
- **ORM:** Django ORM only — no raw SQL unless unavoidable
- **Packages:** `psycopg2-binary`, `python-dotenv`, `whitenoise`, `django-jazzmin`, `together==2.14.0`, `pgvector`, `pypdf`, `python-docx`, `msal` (last 4 added for Module 3 RAG)

### Frontend
- **CSS:** Bootstrap 5 · **Templating:** Django templates (NOT Jinja2) · No JS framework

### Server (On-Premise)
Windows Server 2016 — Intel Xeon Bronze 3106, 32 GB RAM, 4 TB HDD, **no GPU**

### Hosting (Hetzner CX23 — permanent — see Section 8)

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

**Custom permissions:** `can_manage_users`, `can_view_user_list`. Auto-assigned by `aegis/signals.py` `post_save` signal based on role + team. Superusers bypass all permission checks. Signal clears and resets permissions on every user save.

### Product (database)
2,117 rows total. Fields: `category` (main/rolling/plate), `make` (manufacturer, 14 choices, blank for existing rows), `sub_type` (angle/channel/ub/uc/beam/flat/red_material/tmt/pipe/billet/rail/wire/scrap), `size`, `length` (24 choices), `grade` (27 choices), `godown`, `site` (site_1/site_2), `quantity` (T), `rate` (₹/T), `pieces`, `hsn_code`, `is_active`.

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
`quotation_number` (auto: `QT-00001`, `QT-00001-v2`), `lead` FK, `version`, `parent_quotation` self-FK (null = root), `status` (draft/approved/sent), `outcome` (win/loss/not_updated — root only, shared across versions), `winning_quotation` self-FK (records exact version that won — see Architecture Decision 14), `stock_deducted` (guards one-time deduction — see Architecture Decision 15), `payment_terms`, `delivery_address`, `transport_extra`, `sgst_percent`, `cgst_percent`, `total_amount`, `valid_until`, `llm_raw_response`, `quotation_notes_raw` (TextField, blank=True), `quotation_notes_clean` (TextField, blank=True — LLM-cleaned version, user-editable; migration 0028).

**Custom permissions:** `can_approve_quotation`.

Broker-sourced (`lead.broker ≠ null`): PDF = "INTERNAL — RATES ONLY".

### QuotationLineItem (quotations)
`quotation` FK, `product` FK (nullable/SET_NULL — NULL for LLM-generated items; must be picker-set for stock deduction to work), `product_name`, `make` (readonly — picker only), `length` (readonly — picker only), `pcs` (readonly+greyed when no pieces), `uom` (ton/kg), `quantity` (3dp), `unit_price` (readonly — JS-calculated from purchase_rate + add-ons), `total_price` (server-side), `discount_pct` (default 0), `notes`.

`final_price` property = `total_price × (1 − discount_pct/100)` — used in `_quotation_context` so taxes and grand total are discount-aware.

### MarketOrder (quotations)
`broker` FK (CASCADE), `lead` FK (SET_NULL, nullable — set when order auto-created from inbound email), `quotation` FK (nullable), `sub_team` (primary/rolling), `product_details`, `quantity`, `status` (new/rate_sent/broker_confirmed/do_pending/completed/cancelled), `rate`, `loading_dock_member` FK, `do_number`, `notes`, `created_by`. `notify_loading_dock` post_save signal fires email to `loading_dock_member` when `status` transitions to `broker_confirmed` (guarded by `update_fields`).

**Custom permissions:** `can_create_market_order`, `can_assign_loading_dock`, `can_update_do`.

### ProductKeyword (quotations)
Maps client trade terms (e.g. "sariya") → canonical product names. `keyword`, `maps_to`, `notes`, `is_active`. `_build_keyword_context()` fetches active keywords and injects them into the LLM system prompt on every draft generation call.

### TeamEmailConfig (quotations)
IMAP credentials per team (unique per team). `team`, `email_address`, `imap_host` (default imap.gmail.com), `imap_username`, `imap_password`, `imap_port` (993), `use_ssl`, `is_active`, `poll_interval_minutes` (default 30), `last_polled_at` (stamped after each real poll run). SMTP fields: `smtp_host` (blank = derive from imap_host), `smtp_port` (default 587), `smtp_use_ssl` (False = STARTTLS), `smtp_username` (blank = use imap_username), `smtp_password` (blank = use imap_password). Outgoing email uses dedicated SMTP fields; falls back to IMAP equivalents if blank.

### Customer (database) — permissions
**Custom permissions:** `can_reassign_customer`.

### Training models (training app — CREATED, migration applied)

**Case (created, migrated):** `title`, `problem_description` (TextField), `context` (TextField — what triggered it), `resolution` (TextField), `departments` (JSONField — list of team slugs e.g. `["team_9", "cs"]`), `customer` (FK → Customer, null=True), `created_by` (FK → CustomUser), `created_at`. Permissions: `view_case` (all), `add/change/delete_case` (lead+admin).

**KnowledgeDocument (created, migrated — migration 0006):** `source_type` (file/text), `file_url` (URLField — OneDrive link after upload), `filename` (CharField — original filename, saved at upload time; migration 0006), `direct_text` (TextField — extracted text for files; paste-in for text type; populated by `processor.py` for both types), `title`, `keywords` (JSONField), `departments` (JSONField), `description` (TextField), `is_processed` (BooleanField, default=False), `processed_at` (DateTimeField, null=True), `uploaded_by` (FK → CustomUser), `uploaded_at`. No `file` field — original file not stored; text extracted at upload time, file optionally uploaded to OneDrive (OneDrive disabled — creds needed). Processing triggered automatically at upload time in `document_create` view.

**DocumentChunk (created, migrated — migration 0005):** `document` (FK → KnowledgeDocument, CASCADE), `chunk_text` (TextField), `embedding` (VectorField, 1024 dimensions — pgvector), `chunk_index` (IntegerField). Used for semantic similarity search in RAG Q&A.

**QuizSet:** `title`, `description`, `departments` (JSONField), `created_by`, `created_at`. **CRUD admin-only** via `add/change/delete_quizset` permissions (QUIZ_MANAGE block).

**Question:** `question_text` (TextField), `correct_answer` (TextField — admin-written; LLM judges user answer against this), `source` (TextField — free text/URL reference to related case or document), `quiz_set` (FK → QuizSet, null=True — null = standalone flat pool question), `departments` (JSONField), `created_by`, `created_at`. **CRUD admin-only** via `add/change/delete_question` permissions (QUIZ_MANAGE block).

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

**Status: PERMANENT — Hetzner CX23 (ferritesteel.janavshah.com + crm.ferrite.in). DNS cutover complete as of 16 Jun 2026. GCP e2-small still running — delete when Hetzner confirmed stable.**

**Infrastructure (Hetzner CX23 — permanent):**
- Server: Hetzner CX23, Nuremberg, Ubuntu 24.04, IP: `178.105.54.223`
- SSH user: `root` (Hetzner default)
- Domain: `ferritesteel.janavshah.com` — A record in janavshah.com DNS, grey cloud
- WSGI: Gunicorn — running at `/var/www/ferite_steel`
- Reverse proxy: Nginx — running, certbot-modified config at `/etc/nginx/sites-enabled/ferite_steel`
- SSL: Let's Encrypt via Certbot — issued, auto-renews, expires 2026-09-11
- Database: PostgreSQL 16 on the same VM (`ferite_steel_db`, user `ferite_user`)
- Static files: WhiteNoise
- PDF: WeasyPrint — installed and working
- GitHub: SSH auth configured — `www-data` key at `/var/www/.ssh/id_ed25519`; remote set to `git@github.com:janav3036/ferrite-steel.git`
- Scheduled tasks: cron for `poll_emails --scheduled` — **configured** on `www-data` crontab (`* * * * *`), logs to `/var/log/poll_emails.log`
- Deploy scripts: `deploy/setup.sh`, `deploy/nginx.conf`, `deploy/gunicorn.service`

**GCP e2-small (to be decommissioned):**
- IP: `35.225.244.81`. crm.ferrite.in DNS already switched to Hetzner (178.105.54.223). Delete GCP VM once Hetzner confirmed stable.

**Known setup gotchas (already fixed in setup.sh):**
- PostgreSQL GRANT must run inside `ferite_steel_db`: `sudo -u postgres psql -d ferite_steel_db -c "GRANT ALL ON SCHEMA public TO ferite_user;"`
- pgvector must be installed at OS level before migrate: `apt install postgresql-16-pgvector`
- Create pgvector extension before migrate: `sudo -u postgres psql -d ferite_steel_db -c "CREATE EXTENSION IF NOT EXISTS vector;"`
- gunicorn is in requirements.txt but must also be `pip install gunicorn` in venv before systemd service starts

**Future deploys:**
```bash
ssh root@178.105.54.223
sudo -u www-data git -C /var/www/ferite_steel pull
source /var/www/ferite_steel/.venv/bin/activate
python /var/www/ferite_steel/manage.py migrate
python /var/www/ferite_steel/manage.py collectstatic --noinput
sudo systemctl restart gunicorn
```

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
8. ~~Does client's office have a static IP?~~ No longer relevant — using GCP VM.
9. What did ConvoGenie say about API access and integration options?
10. What plan is client on — does it include API access?
11. What does client actually want the two systems to do together?
12. Has Meta verification been initiated for WhatsApp Business API?
13. (Module 3) Should uploaded training documents be kept as original files (downloadable), or is extracted text alone sufficient?
14. (Module 3) When a document is uploaded, does it need to be available for Q&A immediately, or is a delay of a few minutes acceptable?
15. (Module 3) Are most questions expected to be in organised quiz sets, or is a flat pool sufficient? What's the rough split?
16. (Module 3 / voice notes) Do salespeople use Chrome or Edge as their primary browser? (Web Speech API requires Chrome/Edge and HTTPS — Safari/Firefox not supported.)

---

## 11. Unresolved Technical Items

Do not proceed with affected modules until resolved.

- **Hosting:** RESOLVED — Hetzner CX23 (178.105.54.223) is permanent host. Both ferritesteel.janavshah.com and crm.ferrite.in now point to Hetzner. DNS cutover complete 16 Jun 2026. Delete GCP e2-small (35.225.244.81) when confirmed stable.
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
- **3C RAG:** TESTED AND WORKING end-to-end on Hetzner. OneDrive lines commented out in `processor.py` — leave commented until live MSAL credentials available. Embedding model: `intfloat/multilingual-e5-large-instruct` (1024-dim, serverless). Chunk size: 300 words.
- **Web Speech API browser compatibility:** Voice dictation on both lead detail and quotation detail require Chrome/Edge + HTTPS. Confirm team browser (client question 16) — Safari/Firefox not supported.

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

### Module 3 — Training + Case Solver (₹20,000) — Phase 3 (architecture designed, implementation starting)
Three parts:
1. **Static Cases** — admin-adds structured case records (title, problem, context, resolution, departments, customer FK). Convert button on quotation notes pre-fills Case form. Cases are also a RAG source.
2. **RAG Q&A** — semi-chatbot, no history. Answers from `KnowledgeDocument` (uploaded PDFs/DOCX/Excel) + `Case` records. Document types: product catalogues, pricing guidelines, SOPs, past cases, company policies, technical steel knowledge, FAQs, competitor notes. pgvector embeddings. LLM via together.ai.
3. **Quiz/Tutorial** — admin creates `Question` records (question + correct answer text). Questions organised into `QuizSet`s or left as standalone flat pool. User answers; LLM judges correctness against admin answer; explains if wrong. Departments filter which questions each team sees.

Architecture: RAG, pgvector, together.ai. Effort: 70–85 hrs.

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
7. **Deployment:** Hetzner CX23 VM (178.105.54.223), Ubuntu 24.04. Gunicorn + Nginx. Let's Encrypt SSL. PostgreSQL on same VM. GitHub SSH auth configured (www-data key). (Migrated from GCP e2-small 13 Jun 2026 — GCP still running pending DNS cutover.)
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
18. **Django custom permissions + role signal for access control:** Feature gates use Django's built-in permission system (`user.has_perm('app.codename')`), not hardcoded role string checks. Custom permissions declared in each model's `Meta.permissions`. `post_save` signal on `CustomUser` (`aegis/signals.py`) auto-assigns the baseline permission set whenever role is set/changed — clears first, then assigns fresh. Superusers bypass all checks. Admin can grant extra permissions without a code change. Team-scoping (queryset filtering) remains code — permissions don't apply there. New models: define permissions in `Meta` from the start. Existing role checks: replace gradually as views are touched, not as a dedicated refactor. **Permission baseline:** member gets create/edit quotations+leads, view/add customers+products; lead adds approve, reassign customer, view user list, assign loading dock; market team (any role) adds create market order; loading_dock adds update DO; admin gets all.
19. **Web Speech API for voice-to-text on quotation notes:** Browser built-in `window.SpeechRecognition` — no external service, no cost. Microphone button populates `quotation_notes_raw` in real-time. Requires Chrome/Edge and HTTPS (production covered by Let's Encrypt; local `runserver` will not work for this feature). LLM cleanup compensates for transcription errors.

---

## 16. Project Root & Directory Structure

```
ferite_steel/                      ← project root
├── ferite_steel/                  ← Django project config
│   ├── settings.py, urls.py, wsgi.py
│   └── ai.py                      ← shared together_client; import here, never instantiate elsewhere
├── aegis/                         ← auth & user management (CustomUser)
│   ├── models.py, views.py, forms.py, urls.py
│   ├── signals.py                 ← post_save on CustomUser; auto-assigns permissions by role + team
│   └── apps.py                    ← ready() imports signals
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
├── training/                      ← Module 3
│   ├── models.py                  ← Case, KnowledgeDocument, DocumentChunk, QuizSet, Question, QuizAttempt
│   ├── views.py                   ← all training views (case, document, quiz, question CRUD + RAG Q&A)
│   ├── forms.py, admin.py, urls.py
│   ├── migrations/                ← 0001–0005 (0005 adds DocumentChunk, refactors KnowledgeDocument)
│   └── services/
│       ├── llm.py                 ← judge_quiz_answer(), rag_answer()
│       ├── extractor.py           ← PDF/DOCX/text → plain text
│       ├── embedder.py            ← text → 1024-dim vectors via together.ai
│       ├── onedrive.py            ← MSAL upload to OneDrive (needs live credentials)
│       └── processor.py           ← orchestrates extract → chunk → embed → upload → mark processed
├── import_products.py             ← one-time; ProductList_updated.xlsx → database.Product (523 rows)
├── import_business_partners.py    ← one-time; Business Partner ALL.xlsx → database.Customer (6,414 rows)
├── docs/urls.md                   ← full URL reference for all apps
├── templates/                     ← all extend base.html
│   ├── base.html                  ← --sb-* CSS variable tokens for per-page sidebar theming
│   ├── dashboard.html, add_user.html, edit_user_role.html
│   ├── registration/              ← login, password reset
│   ├── database/                  ← product_list/add/edit, customer_list/detail/add/edit, broker_list/create
│   ├── quotations/                ← lead_list/detail/create, quotation_list/detail/edit/pdf/select_lead,
│   │                                 market_order_list/create/detail, quotation_send_confirm
│   ├── training/                  ← 21 templates; all include _sb_amber.html for amber sidebar theme
│   │   ├── _sb_amber.html         ← shared include: Syne font + amber --sb-* + --accent overrides
│   │   ├── home.html, case_list/detail/create/edit/confirm_delete.html
│   │   ├── document_list/detail/create/ask/confirm_delete.html
│   │   ├── quiz_list/detail/take/results.html, quiz_set_create/edit/confirm_delete.html
│   │   └── question_create/edit/confirm_delete.html
│   └── guide/                     ← 3 templates; all include _sb_guide.html for forest-green Codex theme
│       ├── _sb_guide.html         ← shared include: Cormorant Garamond + forest --sb-* + --accent overrides
│       ├── core.html              ← /guide/core/ — auth, profile, notifications, chat; admin: user mgmt
│       ├── quotations.html        ← /guide/quotations/ — leads, editor, add-ons, approve/send, outcomes; market: market orders
│       └── training.html          ← /guide/training/ — cases, quizzes, Q&A; admin: managing content
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
| `training` | Module 3 — Case, KnowledgeDocument, DocumentChunk, QuizSet, Question, QuizAttempt — all created and migrated |
| `guide` | User manual — 3 static pages (core, quotations, training); no models; Codex forest-green theme |
| `ares`, `athena`, `hephaestus`, `hermes`, `themis` | Not yet created |

Future apps per module: `credit_risk`, `leads`.

---

## 18. External Services Status

| Service | Status | Notes |
|---------|--------|-------|
| together.ai | Active | `together==2.14.0`; `generate_quotation_draft` tested end-to-end |
| WhatsApp Business API | Pending Meta approval | Client must initiate — do NOT assume live |
| ConvoGenie | Client has account — reviewing | Integration scope TBD (see Section 9) |
| SAP | Deprioritised | Daily Excel replaces direct integration |
| Email (IMAP/SMTP) | **LIVE** | Polling sales@ferrite.in + fcc@ferrite.in; cron running; leads + notifications firing |
| GCP e2-small VM | DNS cut over — pending deletion | crm.ferrite.in now points to Hetzner; delete GCP VM when stable |
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
