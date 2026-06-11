# User Manual — Module 2: Quotation Automator
# Ferrite Steel CRM

**For:** All sales staff (Team 9, CS Team, Market Team)
**Last updated:** June 2026

---

## Table of Contents

1. [Overview](#1-overview)
2. [Leads](#2-leads)
3. [Creating a Quotation](#3-creating-a-quotation)
4. [The Quotation Editor](#4-the-quotation-editor)
5. [Approving a Quotation](#5-approving-a-quotation)
6. [Revising a Quotation](#6-revising-a-quotation)
7. [Recording the Outcome](#7-recording-the-outcome)
8. [Sending a Quotation](#8-sending-a-quotation)
9. [Case Notes & Voice Dictation](#9-case-notes--voice-dictation)
10. [Market Orders (Market Team Only)](#10-market-orders-market-team-only)
11. [Database — Customers, Products, Brokers](#11-database--customers-products-brokers)
12. [Role Permissions Quick Reference](#12-role-permissions-quick-reference)

---

## 1. Overview

Module 2 — the Quotation Automator — is the core of the CRM. It handles:

- Receiving and recording customer enquiries as **Leads**
- Generating AI-assisted quotation drafts
- The full quotation edit → approve → send workflow
- Broker-to-DO logistics via **Market Orders**
- Structured case notes on difficult or unusual deals

Every deal starts with a Lead and ends with a Won or Lost quotation.

---

## 2. Leads

A **Lead** is a customer enquiry — a request for pricing on iron or steel products. Every quotation must start from a lead.

### 2.1 Creating a Lead Manually

1. Go to **Leads** in the top navigation bar
2. Click **+ New Lead**
3. Fill in the form:
   - **Source** — WhatsApp, Email, or Manual Entry
   - **Raw Text** — paste the customer's original message exactly as received
   - **Customer Name, Phone, Email** — fill what you have (not all are required)
   - **Company, Industry, Location** — optional but helpful for AI to read
   - **Broker** — if this lead came through a broker, select them here
4. Click **Save**

### 2.2 Leads Auto-Created from Email

If your team's email inbox is connected, the system checks for new enquiries automatically. When a valid steel product enquiry arrives in the inbox:

- A Lead is created automatically
- The original email text is saved as the Raw Text
- It appears in your lead list with Source = Email

You can also trigger a manual inbox check using the **Poll Inbox** button on the Leads list page (admins and leads only).

> Spam, out-of-office replies, and non-product enquiries are automatically discarded — the system checks for genuine steel enquiries before creating a lead.

### 2.3 Working a Lead

Click any lead in the list to open the Lead Detail page. From here you can:

- See all customer details and the original enquiry text
- View all quotations linked to this lead
- Add case notes (see [Section 9](#9-case-notes--voice-dictation))
- Create a new quotation
- Delete the lead (shows a warning if quotations exist)

### 2.4 Lead Status

| Status | Meaning |
|---|---|
| New | Just received, not yet worked |
| Processing | Being worked — quotation being prepared |
| Quoted | At least one quotation has been sent |
| Closed | Deal done (won or lost) |
| Rejected | Enquiry was not genuine or out of scope |

---

## 3. Creating a Quotation

From a Lead Detail page, click **+ Create Quotation**.

If the system's AI can read the enquiry and match it to products, it will **auto-fill a draft** — line items, quantities, and suggested prices.

> **Always review the AI draft carefully.** The AI provides a starting point. Verify every product, quantity, and price before approving or sending. Products with no match will appear with ₹0 and a "fill manually" note.

---

## 4. The Quotation Editor

The editor has three areas: the header, the line items table, and the totals.

### 4.1 Header Fields

| Field | Notes |
|---|---|
| Customer details | Auto-filled from lead; can be edited |
| Payment Terms | Advance or Cash |
| Delivery Address | Where goods will be delivered |
| Valid Until | Date the quotation expires |
| Transport Extra | Tick if transport cost is included in quoted prices |
| SGST % / CGST % | Set the tax percentages for this order |

### 4.2 Line Items Table

Each row is one product. For each row:

**Selecting a product:**
Click **⌕ pick** to open the product picker modal. Always use the picker — do not type product details manually. The picker fills in:
- Product name, Make, Length, HSN code
- Purchase Rate (from the product database)

**Entering quantity:**
- Enter the **Quantity** and select **UOM** — ton or kg
- The **pcs** (pieces) field activates automatically for products sold by piece; it is greyed out for bulk products

**Setting the price with add-ons:**
Click **⊞ add-ons** to expand 7 pricing inputs for that row:

| Add-on | What it covers |
|---|---|
| Parity | Origin/destination adjustment |
| Cutting | Cutting charges |
| Loading | Loading charges |
| Transport | Transport cost |
| Margin | Your selling margin |
| Interest | Finance/interest charges |
| Commission | Broker or agent commission |

The **Unit Price** updates automatically as you change add-ons. Default values are read from the customer's notes (if set up) — you can override them for this quotation.

> Add-on values are **not saved** — they exist only in the browser for this session. Only the final Unit Price is stored. Each time you open the editor, defaults are re-read from the customer record.

**Discount:**
Enter a **Discount %** if applicable. The line total is reduced by this percentage before tax is applied.

**Notes:**
Add a per-line note if needed (e.g. "subject to stock availability").

### 4.3 Adding a New Line

Click **+ Add Line** at the bottom of the table. A blank row appears — use **⌕ pick** to select the product.

### 4.4 Totals

The Subtotal, SGST, CGST, and Grand Total are calculated automatically. All amounts are in Indian Rupees (₹).

### 4.5 Saving

Click **Save** at any time. The quotation is saved as a **Draft** and is not visible to the customer yet. You can return and edit it as many times as needed before approving.

---

## 5. Approving a Quotation

Only **team leads** and **admins** can approve a quotation.

1. Open the Quotation Detail page
2. Click **Approve**
3. Status changes to **Approved** — the quotation is ready to send

A team member who created a draft should ask their lead to review and approve before it is sent.

---

## 6. Revising a Quotation

If a customer wants changes after receiving a quotation:

1. Open the quotation detail page
2. Click **Revise**
3. A new version is created — e.g. `QT-00001-v2`
4. The original version is preserved exactly as-is
5. Edit the new version and send it

All versions of a quotation are visible on the Lead Detail page. When you record the final outcome (Win), you choose which version won the deal.

---

## 7. Recording the Outcome

Once a deal is closed, record the result on the Quotation Detail page:

| Outcome | When to use |
|---|---|
| **Won** | Customer confirmed the order |
| **Lost** | Customer went elsewhere |
| **Not Updated** | Still uncertain — update later |

When marking **Won**, select which version of the quotation closed the deal.

> **Stock is deducted automatically when you mark Won.** The quantities are permanently removed from inventory. Changing the outcome back to Lost does not restore stock — physical goods have already been allocated.

The outcome is shared across all versions of the same deal — recording Won on v3 also marks the lead as closed.

---

## 8. Sending a Quotation

### 8.1 Standard Send (Non-Broker Lead)

1. Open the approved quotation
2. Click **Send**
3. Review the compose screen — the PDF is attached automatically
4. Edit the email subject or body if needed
5. Click **Confirm & Send**

The customer receives a PDF quotation by email. The quotation status changes to **Sent**.

### 8.2 Broker Lead Send

If the lead came through a broker (i.e. a broker was selected when creating the lead), the system sends a **rates-only text email** — no PDF is attached.

The PDF generated for broker leads is marked **"INTERNAL — RATES ONLY"** and is used for internal reference only, not shared with the broker's customer.

---

## 9. Case Notes & Voice Dictation

The **Case Notes** section on a Lead Detail page lets you record what happened with a difficult or unusual deal — so others can learn from it later and it can be converted into a training case.

### 9.1 Typing Notes

Scroll to the **Case Notes** card on any lead detail page. Type your notes in the **Raw Notes** box and click **Save**.

### 9.2 Voice Dictation

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

Trade terms (e.g. "sariya", "TMT") are automatically corrected to standard product names as you speak.

### 9.3 AI Cleanup

After saving raw notes, click **✦ Clean up with AI**. The system rewrites your rough notes into a clear, professional summary. The cleaned version appears below — you can still edit it manually.

### 9.4 Convert to Case

Once the cleaned notes look right, click **→ Convert to Case** to create a formal Case record visible in the Training module.

---

## 10. Market Orders (Market Team Only)

Market Orders track logistics for orders sourced through brokers. They run separately from the standard quotation flow — this is about fulfilment, not customer pricing.

### 10.1 Creating a Market Order

1. Go to **Market Orders → + New Market Order**
2. Select the **Broker**, **Sub-team** (Primary or Rolling), and fill in product details
3. Save — status is **New**

### 10.2 Market Order Pipeline

| Status | Meaning | Who acts |
|---|---|---|
| New | Order received from broker | Market member |
| Rate Sent | Internal rate shared with broker | Market member |
| Broker Confirmed | Broker agreed to the rate | Broker reply / market member |
| DO Pending | Delivery Order being prepared | Loading dock |
| Completed | DO issued and sent to broker | Loading dock |
| Cancelled | Order cancelled | Any |

Use the action buttons on the Market Order detail page to move through each stage.

### 10.3 Assigning the Loading Dock

Once a broker confirms, a team lead assigns a **Loading Dock member** to the order. That member receives an email notification automatically.

### 10.4 Issuing the DO

1. The loading dock member opens the order
2. Enters the **DO Number**
3. Clicks **Send DO** to email it to the broker
4. The order moves to **Completed**

---

## 11. Database — Customers, Products, Brokers

### Customers

Go to **Database → Customers** to search and view all customer records. Over 6,400 records are pre-loaded.

Click a customer to see their full details, linked quotations, and notes. Use the **Notes** section to record pricing preferences, transport arrangements, or payment history.

Customers are also automatically created or updated when a quotation is saved against a new name.

### Products

Go to **Database → Products** to browse the full product catalogue (523 products).

Use the search bar to find by description, or filter by Sub-type, Make, Length, and Grade using the dropdowns.

> Products with a ₹0 rate will appear in quotations with ₹0 as the price — always verify the rate is filled in. Contact your admin if a product is missing or has the wrong rate.

### Brokers

Go to **Database → Brokers** to manage broker records. Brokers are separate from customers — they send orders rather than receive quotations. Each broker has a name, company, email, and phone number.

---

## 12. Role Permissions Quick Reference

| Action | Member | Lead | Admin |
|---|---|---|---|
| View leads (own team) | ✓ | ✓ | ✓ |
| Create leads | ✓ | ✓ | ✓ |
| Create quotations | ✓ | ✓ | ✓ |
| Approve quotations | — | ✓ | ✓ |
| Send quotations | ✓ | ✓ | ✓ |
| Poll inbox manually | — | ✓ | ✓ |
| Manage customers | ✓ | ✓ | ✓ |
| Reassign customers | — | ✓ | ✓ |
| Add/edit products | — | — | ✓ |
| Create market orders | Market team only | ✓ | ✓ |
| Assign loading dock | — | ✓ | ✓ |
| Issue Delivery Orders | Loading dock | ✓ | ✓ |
