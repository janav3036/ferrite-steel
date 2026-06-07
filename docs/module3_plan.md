# Module 3 — Training + Case Solver: Implementation Plan

**Status:** Architecture locked. Implementation starting Session 14.
**Budget:** ₹20,000 | **Estimated effort:** 70–85 hours

---

## Overview

Module 3 gives staff a way to learn from past problems, test their knowledge, and get answers to operational questions. It has three distinct sub-modules that can be built and delivered independently.

| Sub-module | Name | Effort | Blocked? |
|---|---|---|---|
| 3A | Case Management | ~15 hrs | No |
| 3B | Quiz / Tutorial System | ~15 hrs | No |
| 3C | RAG Q&A | ~40–55 hrs | Yes — see blockers |

---

## Sub-module 3A — Case Management

### What it does
Staff can log resolved problems as structured Case records. A salesperson sees a difficult customer situation → dictates notes on the lead → AI cleans them up → clicks "Convert to Case" → Case form pre-filled → admin reviews and publishes. Other staff can browse cases by department to learn from past situations.

### Models

**Case**
| Field | Type | Notes |
|---|---|---|
| `title` | CharField(255) | Short summary of the problem |
| `problem_description` | TextField | What the issue was |
| `context` | TextField | What triggered it — customer, situation, product |
| `resolution` | TextField | How it was resolved |
| `departments` | JSONField | List of team slugs e.g. `["team_9", "cs"]` |
| `customer` | FK → Customer | Optional link to the customer involved |
| `created_by` | FK → CustomUser | |
| `created_at` | DateTimeField(auto_now_add) | |

### Views needed
- `case_list` — filterable by department; shows all cases visible to the user's team
- `case_detail` — full read-only view of a resolved case
- `case_create` — form; pre-filled when coming from "Convert to Case" on a lead
- `case_edit` — admin/lead only
- `case_delete` — admin only

### URL: `lead_detail` → "Convert to Case"
The "Convert to Case" button on the lead detail page (currently disabled/placeholder) will pass `lead_notes_clean` and `lead.pk` as query params to `case_create`. The create view pre-fills the form from those params.

### Permissions
- Any authenticated user: view cases for their department
- Lead/admin: create, edit, delete cases
- Admin: see all departments

### Session estimate
1.5 sessions

---

## Sub-module 3B — Quiz / Tutorial System

### What it does
Admin creates questions with a "correct answer" text. Questions are grouped into QuizSets (e.g. "New Joinee Induction", "Pricing Policy") or left in a flat pool. Staff answer questions; the LLM judges correctness against the admin's answer and explains what was wrong or right.

### Models

**QuizSet**
| Field | Type | Notes |
|---|---|---|
| `title` | CharField(255) | |
| `description` | TextField(blank) | |
| `departments` | JSONField | Which teams this quiz is for |
| `created_by` | FK → CustomUser | |
| `created_at` | DateTimeField(auto_now_add) | |

**Question**
| Field | Type | Notes |
|---|---|---|
| `question_text` | TextField | The question shown to the user |
| `correct_answer` | TextField | Admin-written; LLM judges user answer against this |
| `source` | TextField(blank) | Free text — reference to a Case, document, or policy |
| `quiz_set` | FK → QuizSet (null=True) | Null = standalone flat pool question |
| `departments` | JSONField | Which teams see this question |
| `created_by` | FK → CustomUser | |
| `created_at` | DateTimeField(auto_now_add) | |

### LLM judging
`judge_quiz_answer(question_text, correct_answer, user_answer)` in `training/services/llm.py`.
Returns `{"correct": bool, "explanation": str}`. Explanation always shown — positive reinforcement when correct, corrective when wrong.

### Views needed
- `quiz_list` — shows QuizSets + flat pool questions visible to the user's department
- `quiz_detail` — shows all questions in a set; user answers one at a time
- `question_answer` — POST: receives answer, calls LLM judge, returns result (AJAX or page reload)

### Permissions
- Any authenticated user: take quizzes for their department
- Lead/admin: create, edit, delete questions and quiz sets

### Session estimate
1.5 sessions

---

## Sub-module 3C — RAG Q&A

### What it does
Staff ask operational questions in plain English. The system searches uploaded documents (PDFs, DOCX, Excel) and Case records using vector similarity, then uses the LLM to compose a grounded answer from retrieved chunks.

### Models

**KnowledgeDocument**
| Field | Type | Notes |
|---|---|---|
| `file` | FileField(upload_to='documents/') | Original file kept (pending client answer Q13) |
| `title` | CharField(255) | |
| `keywords` | JSONField | Admin-tagged terms for filtering |
| `departments` | JSONField | Which teams can access this document |
| `description` | TextField(blank) | What this document covers |
| `is_processed` | BooleanField(default=False) | Has text been extracted and embedded? |
| `processed_at` | DateTimeField(null=True) | |
| `uploaded_by` | FK → CustomUser | |
| `uploaded_at` | DateTimeField(auto_now_add) | |

### Architecture
1. Upload → save file → create `KnowledgeDocument` record with `is_processed=False`
2. Processing (mechanism TBD — see blockers): extract text → chunk → embed via together.ai → store as pgvector vectors
3. Q&A: embed user query → vector similarity search across chunks + Case records → top-k retrieved → LLM composes answer

### pgvector setup
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```
Requires `pgvector` pip package and a new model `DocumentChunk` to store chunk text + embedding vector.

**DocumentChunk** (additional model)
| Field | Type | Notes |
|---|---|---|
| `document` | FK → KnowledgeDocument | |
| `chunk_text` | TextField | |
| `embedding` | VectorField(dimensions=768) | together.ai embedding model output |
| `chunk_index` | IntegerField | Position in original document |

### Blockers — do not build until resolved
- **Client Q13:** Should original files be kept and downloadable, or is extracted text alone sufficient? Affects `FileField` and storage size.
- **Client Q14:** Does processing need to be immediate, or is a delay of a few minutes OK? Determines processing trigger: "Process" button (simple, synchronous) vs. cron job (async). **Do not build the processing pipeline until this is answered.**

### Session estimate
3–4 sessions (most complex sub-module)

---

## Delivery Order

```
3A Case Management  →  3B Quiz System  →  [wait for client answers]  →  3C RAG Q&A
```

3A and 3B can be demoed and handed over while waiting for client confirmation on 3C.

---

## Open Questions (from CLAUDE.md Section 10)

| # | Question | Blocks |
|---|---|---|
| 13 | Keep original uploaded files or extracted text only? | 3C KnowledgeDocument design |
| 14 | Immediate processing or delay OK? | 3C processing pipeline trigger |
| 15 | Quiz sets or flat pool — what's the rough split? | 3B UI priority |
| 16 | Chrome or Edge as primary browser? | Voice dictation (now confirmed Chrome ✓) |
