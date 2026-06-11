# User Manual — Module 1: Base Setup
# Ferrite Steel CRM

**For:** All staff
**Last updated:** June 2026

---

## Table of Contents

1. [Getting Started — Logging In](#1-getting-started--logging-in)
2. [The Dashboard](#2-the-dashboard)
3. [Notifications](#3-notifications)
4. [Team Chat](#4-team-chat)
5. [Your Profile](#5-your-profile)
6. [User Directory](#6-user-directory)
7. [User Management (Admin Only)](#7-user-management-admin-only)
8. [Role & Team Reference](#8-role--team-reference)

---

## 1. Getting Started — Logging In

Open **Chrome** or **Edge** and go to:

```
crm.ferrite.in
```

Enter your **username** and **password**, then click **Log In**. You will be taken to your Dashboard.

### Forgot your password?

Click **"Forgot Password?"** on the login page. Enter your email address and follow the link sent to you.

> **Don't have an account?** Accounts are created only by an admin. You cannot register yourself. Contact your team lead or admin if you need access.

### Logging out

Click your username in the top-right corner of any page, then click **Log Out**.

---

## 2. The Dashboard

After logging in, you land on the Dashboard. It shows a summary of recent activity for your team.

### Stats cards

| Card | What it shows |
|---|---|
| New Leads | Enquiries that haven't been worked yet |
| Open Quotations | Quotations in draft or approved status |
| Won | Deals closed as won |
| Lost | Deals closed as lost |

**Admins and team leads** see counts across all teams.
**Members** see only their own team's data.

### Notifications panel

The right side of the dashboard shows your most recent unread notifications (up to 12). Click any notification to go directly to the relevant record. Click **Mark all as read** to clear the badge.

---

## 3. Notifications

The system sends you automatic notifications when important things happen — a new lead comes in, a quotation is approved, a deal is won or lost, etc.

### The notification bell

The bell icon in the top navigation bar shows a red badge with the count of unread notifications. Click it to open the notifications page.

### Notifications page

Go to **Notifications** (top nav bell) to see your full notification history. Each notification shows:
- An icon indicating the type
- A title and short message
- A link to the relevant record
- Whether it has been read (unread notifications are highlighted)

### Marking as read

- Click any notification to go to the linked record — it is automatically marked as read.
- Click **Mark all as read** to clear all unread notifications at once.

### What triggers a notification

| Event | Who is notified |
|---|---|
| New lead created | Team lead + admin |
| Quotation approved | Quotation creator |
| Quotation won | Team lead + admin |
| Quotation lost | Team lead + admin |
| New case created | Team lead + admin |
| Market order confirmed by broker | Loading dock member + admin |
| DO requested | Loading dock member |
| Market order completed | Market team lead + admin |

---

## 4. Team Chat

The chat feature lets you communicate with your team directly inside the CRM — no need to leave the system for routine coordination.

Go to **Chat** in the top navigation bar to open it. The URL is `/chat/`.

### Channels

You see the following channels:
- **All Staff** — visible to everyone
- **Your team's channel** (e.g. Team 9, CS Team, Market Team) — visible only to your team

Admins see all team channels.

### Sending a message

1. Click the channel you want to post in (left sidebar)
2. Type your message in the text box at the bottom
3. Press **Enter** to send

To write a message across multiple lines, press **Shift + Enter** — this creates a new line without sending.

> The page automatically loads the last 100 messages. New messages from others appear every few seconds without refreshing.

---

## 5. Your Profile

Click your **username** in the top navigation bar to open your profile page. It shows:
- Your name, username, role, and team
- Your phone numbers and employee details

Contact your admin to update your role, team, or other details — you cannot change these yourself.

---

## 6. User Directory

Go to **Directory** (top nav, or from the admin panel) to see a list of all staff members with their roles, teams, and contact details.

> Visible to team leads and admins only.

---

## 7. User Management (Admin Only)

Admin users manage all staff accounts from the **Admin** menu.

### Adding a new user

1. Go to **Admin → Add User** (or click the **+ Add User** button in the User Directory)
2. Fill in:
   - Username, First name, Last name
   - Email address
   - Phone number(s)
   - Team and Role (the Role dropdown filters automatically based on team)
   - Password (communicated to the user separately)
3. Click **Save**

The new user can log in immediately.

### Editing a user's role or team

1. Go to the User Directory
2. Click the user's name
3. Click **Edit Role**
4. Change the team or role and click **Save**

> Changing a user's role automatically resets all their permissions. No manual permission management is needed.

### Approving a user

If a user registered themselves (not yet supported in production — accounts are admin-created only), an admin must approve them before they can log in.

### Deleting a user

From the User Directory, click the user's name and click **Delete**. This action is permanent.

> Do not delete users who have created leads or quotations — their records will lose their creator link. Consider deactivating them instead (contact the developer).

---

## 8. Role & Team Reference

### Teams

| Team | Who |
|---|---|
| Team 9 | IndiaMART / JustDial / TradeIndia / BNL leads |
| CS Team | Customer service |
| Market Team | Broker-sourced logistics orders |
| Corporate Team | Corporate accounts (details TBD) |
| — (no team) | Admins only |

### Roles

| Role | Description |
|---|---|
| Admin | Full access to all teams, users, and settings |
| Lead (Team Lead) | Approves quotations, sees full team data, manages customers |
| Member | Creates and manages their own leads and quotations |
| Primary | Market Team — senior market role |
| Rolling | Market Team — rolling stock specialist |
| Loading Dock | Market Team — issues Delivery Orders |

### What each role can do

| Action | Member | Lead | Admin |
|---|---|---|---|
| View leads (own team) | ✓ | ✓ | ✓ |
| Create leads | ✓ | ✓ | ✓ |
| Create quotations | ✓ | ✓ | ✓ |
| Approve quotations | — | ✓ | ✓ |
| Send quotations | ✓ | ✓ | ✓ |
| View user directory | — | ✓ | ✓ |
| Manage users | — | — | ✓ |
| View all teams' data | — | — | ✓ |
| Reassign customers | — | ✓ | ✓ |
| Create market orders | Market team only | ✓ | ✓ |
| Assign loading dock | — | ✓ | ✓ |
| Issue Delivery Orders | Loading dock | ✓ | ✓ |
| Add/edit products | — | — | ✓ |
| View cases (training) | ✓ | ✓ | ✓ |
| Create/edit cases | — | ✓ | ✓ |
