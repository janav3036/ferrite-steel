# Developer Manual — FERITE-STEEL CRM

**For:** Any developer picking up this project after initial delivery.
**Last updated:** June 2026
**Built by:** Janav (sole developer, Sessions 1–14)

This document explains the full architecture, every design decision, and how to navigate the codebase. Read it before touching anything.

---

## Table of Contents

1. [What This System Is](#1-what-this-system-is)
2. [Tech Stack](#2-tech-stack)
3. [Local Setup](#3-local-setup)
4. [Project Directory Structure](#4-project-directory-structure)
5. [Apps — Purpose and Boundaries](#5-apps--purpose-and-boundaries)
6. [Models Reference](#6-models-reference)
7. [URL Structure](#7-url-structure)
8. [Architecture Decisions (and Why)](#8-architecture-decisions-and-why)
9. [LLM Integration](#9-llm-integration)
10. [Email Pipeline](#10-email-pipeline)
11. [Permission System](#11-permission-system)
12. [Frontend Conventions](#12-frontend-conventions)
13. [Deployment](#13-deployment)
14. [Adding a New Module](#14-adding-a-new-module)
15. [Known Gaps and Tech Debt](#15-known-gaps-and-tech-debt)

---

## 1. What This System Is

FERITE-STEEL is a Django-based CRM and business management system for an iron and steel distribution company. It replaces:
- Manual quoting via WhatsApp/phone
- Gut-feel credit decisions
- Unstructured lead tracking in notebooks and spreadsheets
- Slow salesperson onboarding

It is **not** a generic CRM. Every design decision was made specifically for how this company operates — broker-to-dealer pipeline, daily Excel stock updates, Indian GST structure, and a small team with mixed technical literacy.

### Modules (as of Session 14)

| Module | Status | App |
|---|---|---|
| 1 — Base Setup | Complete | `aegis`, `database` |
| 2 — Quotation Automator | Complete (awaiting live credentials) | `quotations` |
| 3 — Training + Case Solver | In progress | `training` (not yet created) |
| 4 — Credit Risk AI | Planned | `credit_risk` (not yet created) |
| 5 — Lead Ranking + Inventory | Planned | `leads` (not yet created) |
| 6 — Internal AI Chatbot | Planned | TBD |

---

## 2. Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Framework | Django 6.0.3 | Batteries-included; CBVs + FBVs; admin; ORM |
| Language | Python 3.12 | |
| Database | PostgreSQL 16 | Needed for pgvector (Module 3C RAG) |
| ORM | Django ORM only | No raw SQL unless absolutely unavoidable |
| Frontend | Bootstrap 5 + Django templates | No JS framework — client team is non-technical; templates are maintainable |
| PDF | WeasyPrint | Renders HTML templates to PDF server-side; works on Linux without a browser |
| LLM | together.ai (`meta-llama/Llama-3.3-70B-Instruct-Turbo`) | No OpenAI; cost-effective; supports tool use |
| AI SDK | `together==2.14.0` | |
| Static files | WhiteNoise (CompressedManifestStaticFilesStorage) | Serves static without Nginx involvement |
| Admin UI | django-jazzmin | Themed Django admin |
| Env vars | python-dotenv | `.env` file, never committed |
| Server | Hetzner CX22 VPS, Ubuntu 24.04 | Client confirmed off-premise hosting |
| WSGI | Gunicorn | |
| Reverse proxy | Nginx | |
| SSL | Let's Encrypt (Certbot) | |

**Never use:** Pinecone, Qdrant, Chroma, Weaviate (pgvector only), any local LLM or Ollama, any JS framework.

---

## 3. Local Setup

```bash
# 1. Clone the repo
git clone <repo-url>
cd ferite_steel

# 2. Create and activate virtualenv
python3 -m venv .venv
source .venv/bin/activate        # macOS/Linux
.venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create .env in project root (never commit this)
# Required variables:
SECRET_KEY=your-secret-key-here
DEBUG=True
DB_NAME=ferite_steel_db
DB_USER=your-postgres-user
DB_PASSWORD=your-postgres-password
DB_HOST=localhost
DB_PORT=5432
TOGETHER_API_KEY=your-together-api-key

# 5. Create PostgreSQL database
createdb ferite_steel_db

# 6. Run migrations (ALWAYS review makemigrations output before migrate)
python manage.py makemigrations
python manage.py migrate

# 7. Create superuser
python manage.py createsuperuser

# 8. Run dev server
python manage.py runserver
```

### Migration discipline (important)
Always run `makemigrations` first, read the output carefully, then run `migrate`. Never apply migrations blindly. If you see unexpected changes in the diff (fields you didn't touch, model reordering), investigate before applying.

---

## 4. Project Directory Structure

```
ferite_steel/                        ← git root / Django project root
│
├── ferite_steel/                    ← Django project config package
│   ├── settings.py                  ← All settings; env vars via python-dotenv
│   ├── urls.py                      ← Root URL conf; includes all app urls
│   ├── wsgi.py                      ← WSGI entry point for Gunicorn
│   └── ai.py                        ← Shared together_client instance
│                                       ONLY place Together(...) is instantiated
│                                       All LLM services import from here
│
├── aegis/                           ← App: Auth & user management
│   ├── models.py                    ← CustomUser (extends AbstractUser)
│   ├── views.py                     ← Login/logout handled by Django; register,
│   │                                   add_user, edit_user_role, approve_user,
│   │                                   delete_user, user_directory
│   ├── forms.py                     ← CustomUserCreationForm, EditRoleForm
│   ├── admin.py                     ← CustomUser in jazzmin admin
│   ├── signals.py                   ← post_save on CustomUser; auto-assigns
│   │                                   Django permissions based on role + team
│   ├── apps.py                      ← AppConfig.ready() imports signals
│   └── migrations/
│
├── database/                        ← App: Product, Customer, Broker
│   ├── models.py                    ← Product, Customer, Broker
│   ├── views.py                     ← CRUD for all three + _build_product_groups()
│   ├── forms.py
│   ├── admin.py
│   ├── urls.py
│   └── migrations/                  ← 0001–0016
│
├── quotations/                      ← App: Module 2 (core business logic)
│   ├── models.py                    ← Lead, Quotation, QuotationLineItem,
│   │                                   MarketOrder, ProductKeyword, TeamEmailConfig
│   ├── views.py                     ← All quotation, lead, and market order views
│   │                                   _parse_addon_notes(), _deduct_stock(),
│   │                                   _quotation_context() helpers at top
│   ├── forms.py                     ← QuotationForm, LineItemFormSet, etc.
│   ├── admin.py
│   ├── urls.py
│   ├── management/
│   │   └── commands/
│   │       └── poll_emails.py       ← Management command; run via cron every minute
│   │                                   --dry-run flag for testing
│   │                                   --scheduled flag throttles by TeamEmailConfig
│   └── services/
│       ├── llm.py                   ← All LLM calls; never call together.ai from views
│       └── tools/
│           └── pricing.py           ← lookup_pricing tool definition + handler
│
├── training/                        ← App: Module 3 (NOT YET CREATED)
│   └── (to be created)
│
├── templates/                       ← All HTML templates; all extend base.html
│   ├── base.html                    ← Nav, Bootstrap 5 CDN, sidebar, extra_js block
│   ├── dashboard.html
│   ├── add_user.html
│   ├── edit_user_role.html
│   ├── registration/                ← login.html, password_reset_*.html
│   ├── database/                    ← product_list/add/edit, customer_list/detail/
│   │                                   add/edit, broker_list/create
│   └── quotations/                  ← lead_list/detail/create, quotation_list/
│                                       detail/edit/pdf/select_lead,
│                                       market_order_list/create/detail,
│                                       quotation_send_confirm
│
├── docs/                            ← Project documentation
│   ├── urls.md                      ← Full URL reference
│   ├── module3_plan.md              ← Module 3 implementation plan
│   ├── user_manual_quotation_automator.md
│   └── developer_manual.md          ← This file
│
├── import_products.py               ← One-time script; imported 523 products
│                                       from ProductList_updated.xlsx
├── import_business_partners.py      ← One-time script; imported 6,414 customers
│                                       from Business Partner ALL.xlsx
│
├── CLAUDE.md                        ← Instructions for Claude Code AI tool
├── manage.py
├── requirements.txt                 ← Always pinned; run pip freeze after installs
└── .env                             ← Never committed; see Local Setup
```

---

## 5. Apps — Purpose and Boundaries

**Hard rule:** Each app owns its models. Foreign keys across apps are fine (e.g. `quotations` references `database.Customer`), but business logic for a model lives in its own app's views and services.

| App | Owns | Does not do |
|---|---|---|
| `aegis` | CustomUser, auth flow, permissions | Business data |
| `database` | Product, Customer, Broker | Quotation logic |
| `quotations` | Lead, Quotation, MarketOrder, email pipeline, LLM | User management |
| `training` | Case, KnowledgeDocument, QuizSet, Question | Quotation logic |

---

## 6. Models Reference

### CustomUser (aegis)

Extends `AbstractUser`. Key additions:

- `role` — `admin / lead / member / primary / rolling / loading_dock`
- `team` — `team_9 / cs / market / corporate` (nullable for admins)
- `phone`, `branch`, `employee_id`

**Permissions are auto-assigned by a `post_save` signal** in `aegis/signals.py`. Every time a user is saved, the signal clears all custom permissions and re-assigns based on role + team. This means you never manually assign permissions in code — change the role and the permissions follow automatically. See Section 11 for the full permission baseline.

### Product (database)

523 rows imported; rates were all 0 at import — client fills via admin.

**Relational pricing:** A product can point to another product as its `base_product`. Its `effective_rate` property is then `base_product.rate + rate_offset`. This exists because many products are variants of a base (e.g. different grades of the same section). No chaining — a derived product always points directly to a base, never to another derived product.

`_build_product_groups(queryset)` in `database/views.py` builds a nested dict used by both the product list page and the catalog JSON endpoint. It uses `select_related('base_product')` to avoid N+1 queries.

### Customer (database)

6,414 SAP records imported. Auto-upserted (not duplicated) when a quotation is saved — the upsert key is `customer_code`.

The `notes` field has a special convention: anything below the line `--- Pricing Add-ons ---` is parsed by `_parse_addon_notes()` in `quotations/views.py` to set default add-on values when the quotation editor loads. These defaults are **never written back** — they are session-only.

### Lead (quotations)

Entry point for all business activity. Every quotation must belong to a lead.

- `broker` FK — if set, the lead came through a broker. This changes quotation PDF behaviour (INTERNAL ONLY) and email send behaviour (rates-only text, no PDF).
- `lead_notes_raw` / `lead_notes_clean` — for case conversion workflow. Raw = salesperson's rough input (voice transcript). Clean = LLM-cleaned version, editable before converting to Case.

### Quotation (quotations)

- `quotation_number` — auto-generated as `QT-00001`, `QT-00001-v2` etc.
- `parent_quotation` — self-FK; null means this is the root version.
- `outcome` — stored on root quotation only, shared across all versions of the same deal.
- `winning_quotation` — FK to the specific version that won (not just "the deal won").
- `stock_deducted` — boolean guard. Stock is deducted once when outcome = Win. Changing back to Loss does **not** restore stock. Physical inventory already moved.

### QuotationLineItem (quotations)

- `product` FK is nullable. It is **only set via the picker modal**, never by the LLM.
- LLM draft fills `product_name` as free text, `product` remains null.
- Stock deduction skips any line item where `product` is null — salesperson must re-pick after reviewing the LLM draft.
- `unit_price` is calculated client-side (JS) from purchase rate + add-ons. It is the only pricing field persisted. Add-ons are not stored.
- `final_price` property = `total_price × (1 − discount_pct/100)` — used for GST and grand total so discount is applied before tax.

### MarketOrder (quotations)

Tracks the logistics pipeline for broker-sourced orders. Separate from the quotation flow — this is about fulfilment, not pricing.

`notify_loading_dock` is a `post_save` signal that fires only when `status` transitions **to** `broker_confirmed`. It is guarded with `update_fields` to avoid firing on every save.

### ProductKeyword (quotations)

Maps client trade terms (Hindi/local names like "sariya", "patti") to canonical product names. Fetched at every LLM call and injected into the system prompt. Also used by the voice dictation post-processing in the lead detail JS.

### TeamEmailConfig (quotations)

IMAP credentials per team. SMTP host is derived at send time by replacing `imap.` with `smtp.` in the IMAP host — do not store SMTP host separately.

---

## 7. URL Structure

See `docs/urls.md` for the full reference. Root URL conf is `ferite_steel/urls.py`.

Key prefix conventions:
- `/` — aegis (auth, user management)
- `/quotations/` — quotations app (leads, quotations, market orders)
- `/database/` — database app (products, customers, brokers)
- `/training/` — training app (cases, documents, quizzes) — not yet created
- `/admin/` — Django admin (jazzmin)

---

## 8. Architecture Decisions (and Why)

These decisions are locked. Do not propose alternatives unless there is a compelling reason and the client/owner agrees.

### Tool use for live-data LLM calls
Modules 2, 4, 5, and the chatbot need real-time access to the database during LLM reasoning (e.g. looking up current product prices). We use together.ai's function/tool calling — the LLM decides which tool to call, we execute it in Python and feed the result back. This keeps the LLM grounded in live data rather than hallucinating prices.

### RAG for static knowledge (Module 3, Chatbot KB)
Training documents and case records don't change in real time. Vector similarity search (pgvector) retrieves relevant chunks, which are then fed to the LLM as context. No tool loop needed — just retrieve-then-generate.

### No separate vector database
pgvector extension in PostgreSQL stores embeddings alongside relational data. This avoids running a second database service, simplifies backups, and keeps queries in one place. The performance is sufficient for this scale.

### No JavaScript framework
Bootstrap 5 + Django templates only. The client's staff have mixed technical literacy. Django templates are readable, debuggable, and maintainable by a solo developer. React/Vue would add build tooling, bundler config, and a JS-heavy codebase for no benefit at this scale.

### Shared LLM client in `ferite_steel/ai.py`
`Together(...)` is instantiated exactly once. All service layers import `together_client` from `ferite_steel.ai`. This prevents accidental multiple instantiations, makes it easy to swap the client globally, and centralises API key access.

### Per-row pricing add-ons are session-only
The 7 add-on inputs (parity, cutting, loading, transport, margin, interest, commission) are calculated client-side in the browser. Defaults are read from `customer.notes` on page load. Only the final `unit_price` is stored. This avoids a wide schema with many rarely-used columns and keeps the model clean.

### Product FK set only via the picker
The LLM draft fills product names as free text. It does not set the `product` FK on line items. This is intentional — the LLM doesn't know stock levels or the exact product database structure. A salesperson must use the picker to link the FK, which also enables stock deduction on Win. Any line item without a `product` FK is excluded from stock tracking.

### Stock deduction is one-time and irreversible
When outcome = Win, stock is deducted. The `stock_deducted` boolean prevents this happening twice. Changing the outcome back to Loss does not restore stock — physical goods have already moved. This matches real-world inventory behaviour.

### Django custom permissions (not role string checks)
Feature gates use `user.has_perm('app.codename')`, not `if user.role == 'lead'`. A `post_save` signal auto-assigns the baseline permission set for each role. Benefits: admin can grant extra permissions without a code change; permission logic is declarative and in one place; Django's built-in permission system handles superuser bypass automatically. The signal clears and reassigns on every save — so changing a user's role immediately resets their permissions correctly.

### Two-step LLM ingestion
Every inbound message goes through `classify_message(text)` first. Only if it returns True (it's a product inquiry) do we proceed to `generate_quotation_draft()`. This prevents creating junk leads from spam, out-of-office replies, or unrelated emails. Email headers are also pre-filtered before hitting the LLM.

### Win tracks the specific version
`winning_quotation` is a FK to the exact `Quotation` instance that won, not just the lead. A deal may go through 3 revisions. The salesperson picks which revision closed the deal, so historical analysis is accurate.

---

## 9. LLM Integration

All LLM code is in `quotations/services/llm.py`. Never call `together_client` directly from views.

### Functions

| Function | Purpose |
|---|---|
| `classify_message(text)` | Returns True if text is a steel product inquiry. Used before creating a lead from inbound email. |
| `classify_broker_response(text)` | Returns `'confirmation'`, `'counter'`, or `'other'`. Used when a broker replies to a rate we sent. |
| `cleanup_lead_notes(raw_notes)` | Rewrites rough salesperson notes as a clean professional summary. Called from `lead_save_notes` view. |
| `generate_quotation_draft(lead, entity_notes)` | Tool-use loop. Reads lead text, calls `lookup_pricing` as a tool, returns structured line items for the quotation editor. |

### Tool use pattern (generate_quotation_draft)

```
LLM receives: lead text + customer notes + keyword context
LLM decides: call lookup_pricing(product_name, quantity, uom)
We execute: query Product table, return matching rows
LLM receives: results
LLM repeats for each product mentioned
LLM returns: structured JSON with all line items
```

`lookup_pricing` always returns `{"found": bool, "results": [...]}`. Not-found items are included in the draft with `unit_price=0` and a "fill manually" note — never silently dropped.

`ProductKeyword` records are fetched and injected into the LLM system prompt on every call. These map client trade terms to canonical product names (e.g. "sariya" → "TMT Bar") so the LLM can call `lookup_pricing` with the right name.

### Model used
`meta-llama/Llama-3.3-70B-Instruct-Turbo` via together.ai. Defined as `TOGETHER_MODEL` at the top of `llm.py`. Change it in one place to switch models.

---

## 10. Email Pipeline

**Management command:** `python manage.py poll_emails`

Run every minute via cron: `* * * * * /path/to/venv/bin/python manage.py poll_emails --scheduled`

The `--scheduled` flag makes the command check `TeamEmailConfig.poll_interval_minutes` before actually polling. If the interval hasn't elapsed since `last_polled_at`, it exits immediately. This lets cron run every minute without hammering the mail server.

### What it does

1. Loads all active `TeamEmailConfig` records
2. For each team inbox: connects via IMAP SSL, fetches unseen messages
3. Pre-filters by headers (skips auto-replies, delivery failures, etc.)
4. Checks if sender is a known `Broker` via `_find_broker(email_addr)`
5. Calls `classify_message(body)` — if not an inquiry, marks as Seen and skips
6. If broker sender: creates Lead (with broker FK) + MarketOrder
7. If regular sender: creates Lead only
8. Calls `_strip_reply_chain()` to strip Gmail/Outlook quoted history before saving raw text
9. Marks email as Seen
10. Stamps `last_polled_at`

### Broker reply handling

When a broker replies to an email we sent:
- `_find_broker()` matches sender to a Broker record
- `classify_broker_response()` determines if it's a confirmation or counter-offer
- Confirmation: MarketOrder status → `broker_confirmed`, timestamp stamped, loading dock notified via signal
- Counter: reply text appended to Lead notes

### SMTP

SMTP host is derived at send time: `imap_host.replace("imap.", "smtp.")`. Do not configure separately.

---

## 11. Permission System

Custom permissions are declared in each model's `Meta.permissions`. They are auto-assigned by the `post_save` signal in `aegis/signals.py`.

### Signal behaviour

On every `CustomUser` save:
1. Clear all custom permissions for this user
2. Re-assign based on role + team

This means changing a user's role immediately resets their permissions — no manual admin action needed.

### Permission baseline

| Permission | member | lead | market (any role) | loading_dock | admin |
|---|---|---|---|---|---|
| `quotations.can_approve_quotation` | — | ✓ | — | — | ✓ |
| `database.can_reassign_customer` | — | ✓ | — | — | ✓ |
| `aegis.can_view_user_list` | — | ✓ | — | — | ✓ |
| `aegis.can_manage_users` | — | — | — | — | ✓ |
| `quotations.can_create_market_order` | — | — | ✓ | — | ✓ |
| `quotations.can_assign_loading_dock` | — | ✓ | — | — | ✓ |
| `quotations.can_update_do` | — | — | — | ✓ | ✓ |

Superusers bypass all permission checks (Django built-in behaviour).

### In views

```python
if not request.user.has_perm('quotations.can_approve_quotation'):
    return HttpResponseForbidden()
```

Avoid `if request.user.role == 'lead'` — use `has_perm()`. Legacy role checks are being replaced gradually as views are touched.

---

## 12. Frontend Conventions

- All templates extend `base.html`
- `base.html` provides: Bootstrap 5 CDN, navbar (role-gated), sidebar, `{% block content %}`, `{% block extra_js %}`
- Use `{% block extra_js %}` to add page-specific JavaScript (see lead_detail.html for example)
- Bootstrap grid: `container-fluid` in base, `row g-4` for card layouts
- Cards: `card shadow-sm` with `card-header fw-semibold`
- Flash messages: `{% if messages %}` block immediately after page header, uses Bootstrap alert classes
- Forms: POST only; always include `{% csrf_token %}`
- Paginator: use Django's `Paginator` with 25 items per page (customer, lead, quotation lists)
- Currency: `{{ value|floatformat:2 }}` — `intcomma` (humanize) not yet wired

---

## 13. Deployment

**Target:** Hetzner CX22 VPS, Ubuntu 24.04

### Stack

```
Internet → Nginx (port 80/443) → Gunicorn (Unix socket) → Django
                                                          → WhiteNoise (static)
                                                          → PostgreSQL (local)
```

### Steps

```bash
# Server setup
sudo apt update && sudo apt install -y python3.12 python3.12-venv postgresql nginx certbot python3-certbot-nginx
sudo apt install -y libpango-1.0-0 libcairo2  # WeasyPrint dependencies

# PostgreSQL
sudo -u postgres createuser feriteuser
sudo -u postgres createdb ferite_steel_db -O feriteuser

# App
git clone <repo> /var/www/ferite_steel
cd /var/www/ferite_steel
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# .env (fill in real values)
cp .env.example .env

# Collect static and migrate
python manage.py collectstatic --noinput
python manage.py migrate

# Gunicorn systemd service
# /etc/systemd/system/ferite.service
# [Service] ExecStart=/var/www/ferite_steel/.venv/bin/gunicorn ferite_steel.wsgi --workers 3 --bind unix:/run/ferite.sock

# Nginx config: proxy_pass http://unix:/run/ferite.sock
# certbot --nginx -d yourdomain.com

# Cron for email polling
* * * * * /var/www/ferite_steel/.venv/bin/python /var/www/ferite_steel/manage.py poll_emails --scheduled
```

### Checklist before go-live

- [ ] `DEBUG = False` in settings (read from env)
- [ ] `ALLOWED_HOSTS` set to domain/IP
- [ ] All env vars set on VPS
- [ ] `collectstatic` run
- [ ] Migrations applied
- [ ] Gunicorn systemd service active and enabled
- [ ] Nginx configured and SSL obtained
- [ ] Cron for poll_emails active
- [ ] Product rates filled in via admin (all were 0 at import)
- [ ] TMT products added (missing from original import)
- [ ] TeamEmailConfig record created with live Gmail App Password

---

## 14. Adding a New Module

1. Create the app: `python manage.py startapp <appname>`
2. Add to `INSTALLED_APPS` in `settings.py`
3. Define models with `class Meta` including `verbose_name`, `verbose_name_plural`, and `permissions`
4. Register in `admin.py`
5. Create `urls.py` in the app, include it in `ferite_steel/urls.py`
6. For LLM functionality: add functions to a `services/llm.py` in the app, import `together_client` from `ferite_steel.ai`
7. For tool use: add tool definitions in `services/tools/`
8. Create templates in `templates/<appname>/`, extending `base.html`
9. Run `makemigrations`, review output, then `migrate`
10. Update `docs/urls.md`

---

## 15. Known Gaps and Tech Debt

These are known issues deferred for practical reasons. Address before or during the relevant module.

| Issue | Severity | When to fix |
|---|---|---|
| Product rates all 0 (523 products) | High | Before go-live |
| TMT products missing from import | High | Before go-live |
| Pagination missing on customer list (6,400+ rows) | High | Before go-live |
| `transaction.atomic()` on `quotation_outcome` (stock deduction + outcome save) | Medium | Before go-live |
| `django.contrib.humanize` intcomma for ₹ display | Low | Before go-live |
| Django logging config (errors to file) | High | Before production |
| Model-level validators (GST 15-char, PAN 10-char) | Medium | Module 4 |
| Audit logging (`django-auditlog`) | Medium | Module 4 |
| `from datetime import timedelta` in `poll_emails.py` inside handle() | Low | Next touch |
| Legacy `role == 'x'` checks in views | Low | Replace as views are touched |
| WhatsApp ingestion | Blocked | After Meta approval |
| ConvoGenie integration | Blocked | After client meeting |
| Voice Stand-in | Not greenlit | Do not start |
