# Ferite Steel — Project Status

_Last updated: 2026-05-05_

---

## Phase 1 — Base Setup ✅ Complete

### What's built
- Django project at `D:\Programs\ferite_steel\`
- PostgreSQL 16 database `ferite_steel_db` connected
- `CustomUser` model (`role`, `phone`, `branch`, `employee_id`)
- Login / logout
- Dashboard
- `base.html` — Bootstrap 5 navbar with role-based menu (sales / manager / admin)
- User registration with admin approval workflow
- Add user (admin only)
- User directory with role editing (admin only)
- Approve / delete users (admin only)
- Password reset flow (email-based)

### URLs live
| URL | Purpose |
|-----|---------|
| `/login/` | Login page |
| `/logout/` | Logout |
| `/dashboard/` | Dashboard |
| `/register/` | Self-registration (pending admin approval) |
| `/add-user/` | Admin: create a user directly |
| `/directory/` | Admin: view all users |
| `/directory/<id>/edit-role/` | Admin: change a user's role |
| `/approve-user/<id>/` | Admin: activate a pending user |
| `/delete-user/<id>/` | Admin: delete a user |
| `/password-reset/` | Password reset request |
| `/admin/` | Django admin panel |

### Needed from client — Phase 1
- Nothing outstanding.

---

## Phase 2 — Quotation Automator 🔄 Shell Complete

### What's built
- `quotations` app with full model layer:
  - `PricingEntry` — master pricing sheet
  - `Lead` — incoming enquiry (WhatsApp / email / manual)
  - `Quotation` — generated quote document
  - `QuotationLineItem` — individual line items on a quote
- Service layer skeleton:
  - `services/llm.py` — together.ai wrapper (stub, not yet wired)
  - `services/tools/pricing.py` — LLM tool: look up product pricing
- Manual lead entry form at `/quotations/leads/create/`
- Lead list, lead detail, quotation list, quotation detail
- Quotation approval flow (manager / admin only)
- Admin panel registration for all models
- Quotations link live in navbar

### URLs live
| URL | Purpose |
|-----|---------|
| `/quotations/` | Quotation list |
| `/quotations/<id>/` | Quotation detail |
| `/quotations/<id>/approve/` | Approve a draft quotation |
| `/quotations/leads/` | Lead list |
| `/quotations/leads/create/` | Manually enter a lead |
| `/quotations/leads/<id>/` | Lead detail |

### What's still needed — Phase 2

#### To build next (no external dependencies)
- Wire up together.ai in `services/llm.py` — implement `generate_quotation_draft()`
- LLM function calling orchestration — send lead text to LLM, handle tool calls, parse response into `Quotation` + `QuotationLineItem` records
- "Generate Quotation" button on the lead detail page
- Quotation PDF / print export

#### Blocked on external dependencies
- **WhatsApp ingestion** — blocked until Meta approves the WhatsApp Business API
- **Email ingestion** — blocked until client provides email server credentials

---

## What's Needed from the Client — Right Now

| Item | Why it's needed | Blocking |
|------|----------------|---------|
| **WhatsApp Business API approval** | Meta takes 1–3 weeks to approve. Client must initiate this immediately — we cannot do it for them. | WhatsApp lead ingestion |
| **Master pricing sheet** | Must be loaded into `PricingEntry` before LLM can generate accurate quotes. Needed as a spreadsheet (product code, name, category, unit, base price). | LLM quotation generation |
| **Discount rules** | How are discounts calculated? Fixed tiers? Negotiated per customer? The LLM tool needs to know the rules. | LLM quotation generation |
| **Email server credentials** | Host, port, username, password for the company email account used to receive enquiries. | Email lead ingestion |
| **Confirmation: is WhatsApp live?** | Before building the ingestion webhook, confirm Meta approval has come through. | WhatsApp lead ingestion |

---

## Phases 3–7 — Not Started

| Phase | Module | Status | Key blocker |
|-------|--------|--------|-------------|
| 3 | Training + Case Solver (RAG) | Not started | Needs document corpus from client |
| 4 | Credit Risk AI | Not started | — |
| 5 | Lead Ranking + Inventory Intelligence | Not started | SAP version and access method unconfirmed |
| 6 | Internal AI Chatbot | Not started | Client has not confirmed Tier 1 vs Tier 2 |
| 7 | AI Voice Stand-in | Not started | Client has not greenlit this module |
