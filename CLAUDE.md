# FERITE-STEEL — Claude Code Project Context

This file is the single source of truth for Claude Code on every aspect of the
FERITE-STEEL project. Read it fully before doing anything. Never deviate from the
decisions recorded here without explicit instruction from Janav.

---

## 1. What This Project Is

FERITE-STEEL is a Django-based CRM and business management system being built for
an iron and steel distribution company. It replaces manual quoting, gut-feel credit
decisions, unstructured lead management, and slow salesperson onboarding with an
automated, AI-assisted web system.

This is a paid client engagement managed solely by Janav, a second-year student
developer. The client CEO is taking a chance on Janav based on a personal connection.
Trust is being built incrementally through phased delivery. Every architectural
decision must be defensible to a non-technical client.

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

## 3. Tech Stack

### Backend
- **Framework:** Django (currently 6.0.4 — verify before assuming)
- **Python:** 3.12
- **Database:** PostgreSQL 16, database name `ferite_steel_db`
- **ORM:** Django ORM only — no raw SQL unless unavoidable

### Frontend
- **CSS Framework:** Bootstrap 5 (CDN or local, confirm before adding dependencies)
- **Templating:** Django templates (Jinja2 is NOT used)
- **No frontend framework** (no React, Vue, etc.) — server-side rendered HTML only

### Deployment Target
- **OS:** Windows Server 2016 (on-premise, at client site)
- **CPU:** Intel Xeon Bronze 3106 (8-core, 1.7 GHz, no AVX-512, no GPU)
- **RAM:** 32 GB
- **Storage:** 4 TB HDD
- **Web Server:** IIS + Waitress (Python WSGI server for Windows)
- **No GPU** — local AI inference is completely impossible

### AI / LLM
- **Provider:** together.ai (cloud API — primary for all LLM inference)
- **Why:** Server has no GPU; all AI workloads must be cloud API-based
- **Architecture split:**
  - Tool use / function calling → live-data modules (Quotation Automator,
    Credit Risk AI, Lead Ranking, Inventory Intelligence, Chatbot live queries)
  - RAG (Retrieval-Augmented Generation) → static knowledge modules
    (Training + Case Solver, Chatbot knowledge base)
- **No MCP server** — Django-native tool use is used instead (simpler, no extra
  infrastructure)
- **No local model hosting** of any kind

### Database Tools
- **Primary:** DataGrip 2025.1.3
- **Secondary:** pgAdmin 4 (retained for reference)

### External Integrations (future phases)
- **SAP:** Customer/inventory data for Lead Ranking and Inventory Intelligence
  (access level unconfirmed — see Phase 5 notes)
- **WhatsApp Business API:** Lead ingestion for Quotation Automator
  (Meta verification pending — critical external dependency)
- **Email:** Lead ingestion for Quotation Automator
- **Twilio / Deepgram / ElevenLabs:** Only if AI Voice Stand-in is greenlit

---

## 4. Project Root & Directory Structure

```
D:\Programs\ferite_steel\          ← project root (Windows Server path)
│
├── ferite_steel\                  ← Django project config package
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── aegis\                         ← auth/user management app
│   ├── models.py                  ← CustomUser model lives here
│   ├── views.py                   ← login, logout, dashboard views
│   └── ...
│
├── templates\                     ← global templates directory
│   └── (dashboard.html exists — temporary, base template not built yet)
│
├── manage.py
└── requirements.txt
```

**Shell/terminal context:** When giving commands, assume the working directory is
`D:\Programs\ferite_steel\` unless stated otherwise. Use `python manage.py` not
`python3 manage.py` (Windows convention).

---

## 5. Commands

```bash
# Activate virtual environment (Windows)
source venv/Scripts/activate

# Install dependencies
pip install -r requirements.txt

# Run development server (http://127.0.0.1:8000/)
python manage.py runserver

# Database — always review makemigrations output before running migrate
python manage.py makemigrations
python manage.py migrate

# Tests
python manage.py test                        # all tests
python manage.py test aegis                  # single app
python manage.py test aegis.tests.TestClass  # single test class

# Admin
python manage.py createsuperuser

# Production
python manage.py collectstatic --noinput
```

---

## 6. What Has Been Built (Phase 1 — Complete)

Phase 1 is finished. Do not re-do or suggest re-doing any of the following:

- Django project created at `D:\Programs\ferite_steel\`
- PostgreSQL 16 database `ferite_steel_db` created and connected
- `CustomUser` model in the `aegis` app with fields:
  - `role` (user role/permission level: `sales`, `manager`, `admin`)
  - `phone`
  - `branch`
  - `employee_id`
- Login view at `/login/` — Bootstrap 5 styled page
- Logout view
- Dashboard view — `LOGIN_REDIRECT_URL = '/dashboard/'`
- Templates directory at `D:\Programs\ferite_steel\templates\`
- `dashboard.html` exists but is **temporary** — a proper base template has NOT
  been built yet

**What is still missing from Phase 1 infrastructure:**
- A proper `base.html` base template (Bootstrap 5 navbar, sidebar, block structure)
- Any navigation or layout shell beyond the login page

---

## 7. Modules — Full Specification

### Module 1 — Base Setup (₹5,000)
Django project scaffold, PostgreSQL connection, CustomUser, login/logout, role-based
access groundwork, base template. **Status: Complete except base template.**

---

### Module 2 — Quotation Automator (₹25,000) — Phase 2, Weeks 3–7
**Purpose:** Parse incoming leads from WhatsApp, email, and phone call transcripts.
Match them against a master pricing sheet. Generate a draft quotation using an LLM.

**Inputs:**
- WhatsApp messages (via WhatsApp Business API — Meta approval pending)
- Emails (via Django email parsing or IMAP polling)
- Phone call transcripts (deferred to later; voice input not in Phase 2)

**Core logic:**
1. Ingest raw lead text (product name, quantity, location, urgency signals)
2. Call together.ai LLM with tool use / function calling
3. Tools available to the LLM: look up master pricing sheet, apply discount rules,
   check product availability (if SAP is connected by then — otherwise static)
4. LLM returns structured quotation draft
5. Sales rep reviews and approves before sending

**Key external dependency:** WhatsApp Business API Meta verification (1–3 week
delay). Client must initiate this immediately. Do not assume it is available.

**Architecture:** Tool use / function calling (NOT RAG). Live data lookup.

**Estimated effort:** ~90–110 hours.

---

### Module 3 — Training System + Case Solver (₹20,000) — Phase 3, Weeks 8–11
**Purpose:** Combined unit. Sales staff can ask questions about products, processes,
and past solved cases. System retrieves relevant knowledge from a static document
corpus.

**Architecture:** RAG (Retrieval-Augmented Generation)
- Document corpus: product manuals, internal SOPs, solved case library, price
  negotiation guides
- Embedding model: cloud API (together.ai or compatible) — no local embeddings
- Vector store: pgvector (PostgreSQL extension) — keeps everything in the existing
  DB, no separate vector DB infrastructure needed
- LLM: together.ai for answer generation

**Schedule risk:** This is Janav's first RAG implementation. Build time may exceed
estimates. Do not compress the schedule here.

**Estimated effort:** ~70–85 hours.

---

### Module 4 — Credit Risk AI (₹20,000) — Phase 4, Weeks 12–15
**Purpose:** Assess customer default risk before extending credit. Replaces
gut-feel decisions.

**Inputs:**
- Financial documents (balance sheets, P&L — uploaded as PDF/image)
- GST return data (uploaded or typed)
- Internal transaction history (from ferite_steel_db)

**Architecture:** Tool use / function calling
- LLM analyzes structured financial signals via tool calls
- Returns a risk score with reasoning

**Estimated effort:** ~60–75 hours.

---

### Module 5 — Lead Ranking + Inventory Intelligence (₹30,000) — Phase 5, Weeks 16–18
**Purpose:** Rank incoming leads by conversion likelihood. Surface inventory
insights tied to customer demand patterns.

**Architecture:** Tool use / function calling. SAP is the primary data source.

**Critical dependency — SAP integration (must confirm with client before Phase 5):**
- SAP version: ECC vs S/4HANA (affects which integration method is available)
- Whether other systems already pull SAP data and how
- Whether SAP Gateway or Integration Suite is active
- Whether SAP is managed in-house or by an external vendor

**SAP integration options (in order of preference/cost):**
1. **PyRFC** — direct RFC calls to SAP. Default safest/cheapest. Requires SAP
   authorization and network access from the Django server.
2. **OData** — free if SAP Gateway is already active. Clean REST interface.
3. **SAP Integration Suite** — expensive if not already licensed. Avoid unless
   already in place.

**Estimated effort:** ~65–100 hours (wide range reflects SAP access uncertainty).

---

### Module 6 — Internal AI Chatbot (₹18,000–22,000, Tier 1 baseline)
**Purpose:** Staff can ask questions across all modules in natural language.

**Tiers (client intent unconfirmed — must ask before finalizing):**
- Tier 1 (₹18K–22K, 2.5–3.5wk): RAG + tool use, simple Q&A across all modules
- Tier 2 (₹30K–40K, 5–7wk): Multi-step conversational, memory within session
- Tier 3: Claude Enterprise + MCP — don't build, just configure

**Architecture:** Hybrid RAG + tool use depending on query type.

---

### Module 7 — AI Voice Stand-in (proposed, NOT greenlit, quoted separately)
**Purpose:** When a salesperson line is busy, an AI answers, conducts a basic
conversation, and logs the lead.

**Tiers:**
- Tier 1 (₹15K–20K, 2–3wk): Voicemail-to-text + auto-reply. No real-time voice.
- Tier 2 (₹40K–60K, 5–8wk): Real-time AI with generic synthetic voice.
- Tier 3 (₹80K–1,20,000+, 10–14wk): Cloned salesperson voice + full conversation.

**Tech stack if built:** Twilio (telephony), Deepgram (STT), ElevenLabs (TTS/voice
cloning), together.ai or OpenAI (LLM backbone).

**Legal risks (Tier 3 especially):**
- Written consent required from salesperson for voice cloning
- Caller disclosure required (IPC S.416 impersonation risk)
- Call transcriptions are personal data under DPDPA 2023
- AI commercial commitments may be legally binding
- Salesperson reputation risk if AI errs

Do NOT start any Voice Stand-in work until client greenlights a specific tier.

---

## 8. Phased Delivery & Schedule

| Phase | Weeks       | Module                          | Hours Est.  | Key Risks                          |
|-------|-------------|---------------------------------|-------------|------------------------------------|
| 1     | 1–2         | Base Setup                      | 40–50       | None — complete                    |
| 2     | 3–7         | Quotation Automator             | 90–110      | WhatsApp API approval delay        |
| 3     | 8–11        | Training + Case Solver          | 70–85       | First RAG build — time risk        |
| 4     | 12–15       | Credit Risk AI                  | 60–75       | PDF parsing reliability            |
| 5     | 16–18       | Lead Ranking + Inventory Intel  | 65–100      | SAP access quality unknown         |
| 6     | +6–8wk      | AI Voice Stand-in (if greenlit) | TBD by tier | Legal, Meta/Twilio approvals       |
| 7     | +2.5–3.5wk  | Internal AI Chatbot             | 55–70       | Tier TBD by client                 |

**Contractual deadline:** ~September (exact date per signed agreement).

**Additional schedule risks:**
- Janav's college exam weeks — must be factored into timeline
- WhatsApp Business API: 1–3 week Meta verification. Client must start this NOW.

---

## 9. Fee Structure

| Module                          | Fee            |
|---------------------------------|----------------|
| Base Setup                      | ₹5,000         |
| Quotation Automator             | ₹25,000        |
| Training + Case Solver          | ₹20,000        |
| Credit Risk AI                  | ₹20,000        |
| Lead Ranking + Inventory Intel  | ₹30,000        |
| **Core Total**                  | **₹1,00,000**  |
| Internal AI Chatbot (Tier 1)    | ₹18,000–22,000 |
| AI Voice Stand-in               | Quoted separately by tier |

All API/infrastructure costs (together.ai, WhatsApp Business API, Twilio, etc.)
are borne by the client, not Janav.

---

## 10. Architecture Decisions — Locked, Do Not Re-Litigate

These decisions are final. Do not suggest alternatives unless Janav explicitly asks
to reconsider.

1. **Tool use / function calling** for all live-data modules (2, 4, 5, Chatbot live
   queries). LLM calls Django-defined tools at inference time.

2. **RAG** for static knowledge modules (Training + Case Solver, Chatbot knowledge
   base). pgvector is the vector store — no separate Pinecone/Weaviate/Qdrant.

3. **No local LLM** of any kind. Server hardware cannot support it. together.ai is
   the sole LLM provider. All embedding workloads also go to cloud APIs.

4. **No MCP server.** Django-native tool use is the equivalent. MCP is unnecessarily
   complex for this environment.

5. **IIS + Waitress** for deployment on Windows Server 2016. No Linux VM unless
   Janav explicitly decides to change this.

6. **PostgreSQL 16 + pgvector** for all data including vector embeddings. No
   separate vector database.

7. **Bootstrap 5 + Django templates** for all UI. No JavaScript framework.

---

## 11. Open Decisions (Do Not Assume Resolved)

These are unresolved. If a task touches any of these areas, flag the dependency
and ask Janav before proceeding.

- **WhatsApp Business API status:** Has Meta approval come through? Do not build
  WhatsApp ingestion until confirmed live.
- **SAP access details:** Version, integration method, network access from server.
  Required before any Phase 5 work.
- **Internal AI Chatbot tier:** Client has not confirmed Tier 1 vs 2. Do not finalize
  chatbot scope without this.
- **AI Voice Stand-in:** Not greenlit. Do not plan or scaffold anything for this.
- **Base template:** `base.html` has not been built yet. This is the first thing
  needed before any new pages are added.

---

## 12. Database

- **Engine:** PostgreSQL 16
- **Database name:** `ferite_steel_db`
- **Host:** localhost (on the Windows Server)
- **Django app managing auth:** `aegis`
- **CustomUser model location:** `aegis.models.CustomUser`
- **CustomUser extra fields:** `role`, `phone`, `branch`, `employee_id`
- **AUTH_USER_MODEL** in settings.py: `'aegis.CustomUser'`
- **pgvector** will be needed from Phase 3 onward — not installed yet

**Migration discipline:** Never run `migrate` without first reviewing what
`makemigrations` generated. Always check migration files before applying.

### Environment variables

Required in `.env` (never commit this file):

```
SECRET_KEY=
DEBUG=
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=
```

---

## 13. Settings & Configuration Notes

- `LOGIN_REDIRECT_URL = '/dashboard/'`
- `LOGIN_URL = '/login/'`
- Templates directory: `D:\Programs\ferite_steel\templates\`
- Static files: not yet fully configured for production (Waitress + IIS will need
  `collectstatic` and IIS to serve `/static/`)
- `DEBUG` must be `False` in production — never deploy with `DEBUG = True`
- Secret key must come from environment variable, not hardcoded in settings.py

### REST Framework defaults

```python
DEFAULT_AUTHENTICATION_CLASSES: [SessionAuthentication]
DEFAULT_PERMISSION_CLASSES:      [IsAuthenticated]
```

All API endpoints require authentication unless explicitly overridden.

---

## 14. URLs Defined So Far

| URL          | View           | App   |
|--------------|----------------|-------|
| /login/      | login view     | aegis |
| /logout/     | logout view    | aegis |
| /dashboard/  | dashboard view | aegis |

---

## 15. App Structure

The project uses six domain apps named after Greek mythological figures. Only
`aegis` has substantial code; the others are scaffolds.

| App           | Purpose                                      |
|---------------|----------------------------------------------|
| `aegis`       | Authentication & user management — CustomUser |
| `ares`        | (not yet implemented)                        |
| `athena`      | (not yet implemented)                        |
| `hephaestus`  | (not yet implemented)                        |
| `hermes`      | (not yet implemented)                        |
| `themis`      | (not yet implemented)                        |

Future apps to be created per module: `quotations`, `credit_risk`, `training`, `leads`.

---

## 16. What To Build Next (After Base Template)

Priority order:
1. **`base.html`** — Bootstrap 5 base template with navbar, sidebar scaffold,
   `{% block content %}`, and `{% block title %}`. All other templates extend this.
2. **Role-based navigation** — different menu items based on `request.user.role`
3. **Phase 2 scaffold** — Quotation Automator app (`quotations`), models, URL
   routing — only after WhatsApp API status is confirmed

---

## 17. Coding Conventions

- Follow Django best practices throughout
- One Django app per major module (e.g., `aegis`, `quotations`, `credit_risk`,
  `training`, `leads`)
- Models: use `class Meta` with `verbose_name` and `verbose_name_plural`
- Views: prefer class-based views (CBVs) for CRUD, function-based views (FBVs)
  for custom logic
- All LLM calls go through a single service layer (e.g., `services/llm.py`) —
  never call together.ai directly from views
- All tool definitions for function calling go in `services/tools/` directory
- Environment variables via `python-decouple` or `os.environ` — never hardcode
  secrets
- Requirements must be pinned (`pip freeze > requirements.txt` after each
  install session)

---

## 18. Windows Server Deployment Notes

- Python installed system-wide or in a venv at a fixed path
- Waitress serves Django WSGI; IIS acts as reverse proxy in front of Waitress
- IIS serves `/static/` and `/media/` directly (not through Django/Waitress)
- `collectstatic` must be run before deployment: `python manage.py collectstatic --noinput`
- Windows Firewall rules needed for port 8000 (Waitress) and 80/443 (IIS)
- PostgreSQL service must be set to start automatically on Windows boot
- Waitress must be run as a Windows Service (use `pywin32` or NSSM wrapper)

---

## 19. Key External Services & Their Status

| Service                  | Status                        | Notes                                      |
|--------------------------|-------------------------------|--------------------------------------------|
| together.ai              | Active (client pays)          | Primary LLM API for all modules            |
| WhatsApp Business API    | Pending Meta approval         | Client must initiate — do NOT assume live  |
| SAP                      | Access unconfirmed            | Version and method TBD before Phase 5      |
| Email (IMAP/SMTP)        | To be configured in Phase 2   | Client email server details needed         |
| Twilio                   | Not started                   | Only if Voice Stand-in is greenlit         |
| Deepgram                 | Not started                   | Only if Voice Stand-in is greenlit         |
| ElevenLabs               | Not started                   | Only if Voice Stand-in is greenlit         |

---

## 20. Non-Negotiables (Things That Must Never Happen)

- Never suggest running a local LLM, downloading model weights, or using
  Ollama/llama.cpp — the server has no GPU
- Never suggest a separate vector database (Pinecone, Qdrant, Weaviate, Chroma) —
  pgvector in PostgreSQL is the decision
- Never suggest replacing IIS + Waitress with Nginx/Gunicorn unless Janav asks
- Never commit secrets to version control
- Never deploy with DEBUG = True
- Never skip migration review before applying
- Never add a frontend JavaScript framework
- Never build anything for Voice Stand-in until client greenlights a specific tier
- Never assume WhatsApp API is live — always check with Janav first
