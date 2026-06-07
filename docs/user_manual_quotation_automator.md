# User Manual — Quotation Automator (Module 2)
# Ferrite Steel CRM

**For:** All staff (Team 9, CS Team, Market Team)
**Last updated:** June 2026

---

## Table of Contents

1. [Logging In](#1-logging-in)
2. [The Dashboard](#2-the-dashboard)
3. [Leads](#3-leads)
4. [Quotations](#4-quotations)
5. [Sending a Quotation](#5-sending-a-quotation)
6. [Market Orders (Market Team Only)](#6-market-orders-market-team-only)
7. [Case Notes & Voice Dictation](#7-case-notes--voice-dictation)
8. [Database — Customers, Products, Brokers](#8-database--customers-products-brokers)
9. [Role Permissions Quick Reference](#9-role-permissions-quick-reference)

---

## 1. Logging In

Open your browser (Chrome or Edge recommended) and go to the system URL provided by your administrator.

- Enter your **username** and **password**
- Click **Log In**
- You will be taken to your Dashboard

If you forget your password, click **"Forgot Password?"** on the login page and follow the email instructions.

> **First time?** Your account is created by an admin. You cannot self-register. Contact your team lead or admin if you don't have access.

---

## 2. The Dashboard

The dashboard shows a summary of recent activity for your team:

- **New Leads** — enquiries that haven't been worked yet
- **Open Quotations** — quotations in draft or approved status
- **Won / Lost** — outcome counts for closed quotations

Admins and team leads see all records across all teams. Members see only their own records.

The top navigation bar has links to:
- **Quotations** — your quotation list
- **Leads** — your lead list
- **Database** — customers, products, brokers
- **Market Orders** (market team only)

---

## 3. Leads

A **Lead** is a customer enquiry — a request for pricing on iron or steel products. Every quotation must start from a lead.

### 3.1 Creating a Lead Manually

1. Go to **Leads** in the top navigation
2. Click **+ New Lead**
3. Fill in the form:
   - **Source** — WhatsApp, Email, or Manual Entry
   - **Raw Text** — paste the customer's original message exactly as received
   - **Customer Name, Phone, Email** — fill what you have; not all are required
   - **Company, Industry, Location** — optional but helpful for context
   - **Broker** — if this lead came through a broker, select them here
4. Click **Save**

### 3.2 Leads from Email

If your team's email inbox is connected, the system checks for new enquiries automatically. When a valid steel product enquiry arrives:
- A Lead is created automatically
- The original email text is saved as the Raw Text
- You will see it appear in your lead list with Source = Email

You can also trigger a manual inbox check from the Leads list page using the **Poll Inbox** button (admin and lead roles only).

### 3.3 Working a Lead

Click any lead in the list to open the Lead Detail page. From here you can:

- See all customer details and the original enquiry text
- View all quotations linked to this lead
- Add case notes (see [Section 7](#7-case-notes--voice-dictation))
- Create a new quotation
- Delete the lead (with a warning if quotations exist)

### 3.4 Lead Status

| Status | Meaning |
|---|---|
| New | Just received, not yet worked |
| Processing | Being worked — quotation being prepared |
| Quoted | At least one quotation has been sent |
| Closed | Deal done (won or lost) |
| Rejected | Enquiry was not genuine or out of scope |

---

## 4. Quotations

### 4.1 Creating a Quotation

From a Lead Detail page, click **+ Create Quotation**. This opens the quotation editor.

If the system's AI can read the enquiry and match products, it will **auto-fill a draft** — line items, quantities, and suggested prices. Review every line carefully before proceeding.

> **Important:** The AI draft is a starting point, not a final quotation. Always verify products, quantities, and prices.

### 4.2 The Quotation Editor

The editor has three areas:

**Header fields**
- Customer details (auto-filled from lead; can be edited)
- Payment Terms, Delivery Address, Valid Until date
- Transport Extra (tick if transport is included in price)
- GST % (SGST and CGST)

**Line Items table**
Each row is one product. For each row:
- Click **⌕ pick** to open the product picker modal — always use this to select products
- The picker fills in: Product, Make, Length, HSN code, and Purchase Rate automatically
- Enter **Quantity** and select **UOM** (ton or kg)
- Click **⊞ add-ons** to expand pricing inputs for that row:
  - Parity, Cutting, Loading, Transport, Margin, Interest, Commission
  - The Unit Price updates automatically as you change these
- Enter **Discount %** if applicable (reduces the line total)
- Add a **Note** if needed (e.g. "subject to availability")

> **Pieces field:** For products sold by piece, the `pcs` field is active. For bulk products, it is greyed out automatically.

**Totals**
- Subtotal, SGST, CGST, and Grand Total are calculated automatically
- All amounts are in Indian Rupees (₹)

### 4.3 Adding a New Line

Click **+ Add Line** at the bottom of the table. A blank row appears — use **⌕ pick** to select the product.

### 4.4 Saving

Click **Save** at any time. The quotation is saved as a **Draft** and is not visible to the customer yet.

### 4.5 Approving a Quotation

Only **team leads** and **admins** can approve a quotation. Once approved, the status changes to **Approved** and it is ready to send.

To approve: open the Quotation Detail page and click **Approve**.

### 4.6 Revising a Quotation

If a customer wants changes after receiving a quotation:

1. Open the quotation detail page
2. Click **Revise**
3. A new version is created (e.g. QT-00001-v2) — the original is preserved
4. Edit the new version and send it

All versions of a quotation are visible on the Lead Detail page.

### 4.7 Recording the Outcome

Once a deal is closed, open the quotation and record the outcome:

- **Won** — you got the order. Select which version won (important if you revised).
- **Lost** — the customer went elsewhere.
- **Not Updated** — deal is still uncertain; update later.

> **Stock note:** Marking a quotation as Won automatically deducts the quantities from the product inventory. This is a one-time, permanent action. Changing the outcome back does not restore stock.

---

## 5. Sending a Quotation

### 5.1 Standard Send (Non-Broker Lead)

1. Open the approved quotation
2. Click **Send**
3. Review the compose screen — the PDF is attached automatically
4. Edit the email subject or body if needed
5. Click **Confirm & Send**

The customer receives a PDF quotation by email. The quotation status changes to **Sent**.

### 5.2 Broker Lead Send

If the lead came through a broker, the system sends a **rates-only text email** (no PDF). The PDF generated for broker leads is marked "INTERNAL — RATES ONLY" and is not shared externally.

---

## 6. Market Orders (Market Team Only)

Market Orders track logistics for orders sourced through brokers. They run separately from the standard quotation flow.

### 6.1 Creating a Market Order

1. Go to **Market Orders** → **+ New Market Order**
2. Select the Broker, Sub-team (Primary or Rolling), and fill in product details
3. Save — status is **New**

### 6.2 Market Order Pipeline

| Status | Meaning | Who acts |
|---|---|---|
| New | Order received from broker | Market member |
| Rate Sent | Internal rate sent to broker | Market member |
| Broker Confirmed | Broker has agreed to the rate | Broker reply / market member |
| DO Pending | Delivery Order being prepared | Loading dock |
| Completed | DO issued and sent to broker | Loading dock |
| Cancelled | Order cancelled | Any |

Progress through each stage using the action buttons on the Market Order detail page.

### 6.3 Assigning the Loading Dock

Once a broker confirms, a team lead assigns a **Loading Dock member** to the order. That member receives an email notification automatically.

### 6.4 Issuing the DO

The loading dock member opens the order, enters the **DO Number**, and clicks **Send DO** to email it to the broker. The order moves to **Completed**.

---

## 7. Case Notes & Voice Dictation

The **Case Notes** section on a Lead Detail page lets you record what happened with a difficult or unusual situation — so others can learn from it later.

### 7.1 Typing Notes

Scroll to the **Case Notes** card on any lead detail page. Type your notes in the **Raw Notes** box and click **Save**.

### 7.2 Voice Dictation

Click **🎤 Dictate** to start speaking. Your words appear in the Raw Notes box in real time. Click **⏹ Stop** when done.

**Punctuation by voice:**

| Say | Result |
|---|---|
| "comma" | , |
| "full stop" or "period" | . |
| "question mark" | ? |
| "exclamation" | ! |
| "new line" | line break |
| "colon" | : |
| "dash" | — |

> Voice dictation requires **Chrome or Edge** browser. It will not work in Firefox or Safari.

Trade terms (e.g. "sariya", "TMT", product codes) are automatically corrected to standard names as you speak.

### 7.3 AI Cleanup

After saving your raw notes, click **✦ Clean up with AI**. The system rewrites your rough notes into a clear, professional summary. The cleaned version appears below — you can still edit it manually before saving.

### 7.4 Convert to Case

Once the cleaned notes look right, click **→ Convert to Case** to create a formal Case record that other staff can browse and learn from. *(Available once Module 3 — Training is live.)*

---

## 8. Database — Customers, Products, Brokers

### Customers

Go to **Database → Customers** to search and view all customer records. Over 6,400 records are pre-loaded from SAP.

Click a customer to see their full details, linked quotations, and notes. Use the **Notes** section to record context like pricing preferences, transport arrangements, or payment history.

Customers are also auto-created or updated automatically when a quotation is saved against a new name.

### Products

Go to **Database → Products** to browse the full product catalogue (523 products).

Use the search bar to find by description, or browse by Sub-type, Make, Length, and Grade using the filters. All rates must be filled in by an admin before products can be quoted accurately.

> Products with 0 rate will appear in quotations with 0 as the price — always verify.

### Brokers

Go to **Database → Brokers** to manage broker records. Brokers are separate from customers — they send orders rather than receive quotations. Each broker has a name, company, email, and phone.

---

## 9. Role Permissions Quick Reference

| Action | Member | Lead | Admin |
|---|---|---|---|
| View leads (own team) | ✓ | ✓ | ✓ |
| Create leads | ✓ | ✓ | ✓ |
| Create quotations | ✓ | ✓ | ✓ |
| Approve quotations | — | ✓ | ✓ |
| Send quotations | ✓ | ✓ | ✓ |
| Manage users | — | — | ✓ |
| View all teams' data | — | — | ✓ |
| Create market orders | Market team only | ✓ | ✓ |
| Assign loading dock | — | ✓ | ✓ |
| Issue DO | Loading dock | ✓ | ✓ |
| Add/edit products | — | — | ✓ |
| Reassign customers | — | ✓ | ✓ |
