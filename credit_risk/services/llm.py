import json

from ferite_steel.ai import chat_completion

TOGETHER_MODEL = 'meta-llama/Llama-3.3-70B-Instruct-Turbo'

RISK_BANDS = [(8, 10, 'low'), (4, 7, 'medium'), (1, 3, 'high')]


def _risk_level_for_score(score):
    for lo, hi, level in RISK_BANDS:
        if lo <= score <= hi:
            return level
    return 'high'


def score_from_points(earned, possible):
    """Maps the deterministic points onto the existing 1-10 score field (and
    therefore the existing risk-level bands/medallion UI) via percentage —
    keeps working unchanged if points_possible later grows (e.g. when
    Sales-vs-Purchases gets switched on)."""
    if not possible:
        return None
    pct = earned / possible
    return max(1, min(10, round(pct * 10)))


def background_company_notes(company_names):
    """One batched LLM call using the model's general training knowledge —
    explicitly NOT a live web search (none is wired into this app). Bounded
    to a handful of names (the customer's own top-tier buyers) since this is
    informational context, not a scored mark."""
    if not company_names:
        return {}
    names = company_names[:12]
    prompt = (
        "For each Indian company name below, if you recognise it from your general "
        "training knowledge, give a one-sentence note on what kind of company it is "
        "and, only if you're specifically aware of it, any notable reputation concern "
        "(e.g. reported payment delays, insolvency proceedings, public disputes). If "
        "you don't recognise a name, say so plainly — do not guess or invent details.\n\n"
        'Return ONLY a JSON object mapping each exact company name to '
        '{"note": "...", "reputation_flag": "none"|"caution", "recognised": true|false}.\n\n'
        "Companies:\n" + "\n".join(f"- {n}" for n in names)
    )
    response = chat_completion(
        model=TOGETHER_MODEL,
        messages=[{'role': 'user', 'content': prompt}],
        max_tokens=900,
    )
    raw = response.choices[0].message.content or '{}'
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}


def compute_data_confidence(sales, purchase, notes, quotation_signal):
    """How much the inputs behind a given score are worth trusting —
    computed deterministically, never left to the LLM to self-report."""
    has_trading_data = bool(sales and sales.get('rows')) or bool(purchase and purchase.get('rows'))
    notes_substantial = len((notes or '').strip()) >= 40

    points = 0
    if has_trading_data:
        points += 2
    if notes_substantial:
        points += 1
    if quotation_signal:
        points += 1

    if points >= 3:
        return 'high'
    if points >= 1:
        return 'medium'
    return 'low'


def assess_credit(customer, notes, score_result, background_notes,
                   prior_assessment=None, quotation_signal=None):
    """Score is already final (computed deterministically in services/scoring.py)
    — the LLM only narrates it and picks a recommendation. It must never invent
    or restate a different numeric score."""
    system_prompt = (
        "You are a credit-risk assistant for an iron and steel distribution company in India, "
        "helping a salesperson decide whether to extend trade credit to a customer.\n\n"
        "The numeric score has ALREADY been computed deterministically in Python from a fixed "
        "point rubric — you will be given the exact marks awarded in each category below. Do "
        "NOT invent, restate, or imply a different score. Your job is only to: (1) write a "
        "short narrative summary explaining what the marks mean in plain language, (2) give a "
        "recommendation, and (3) list factors — each one should reference or explain one of "
        "the given marks, the background notes, or the salesperson's own notes, not introduce "
        "new unverified claims of your own.\n\n"
        "The uploaded file is the CUSTOMER's OWN Tally export, not this company's — the 'Sales' "
        "sheet lists companies the customer sold to, the 'Purchase' sheet lists companies the "
        "customer bought from. It has NO ageing/outstanding-balance/payment-delay data — rely "
        "on the salesperson's notes for actual payment behaviour; if the notes don't mention "
        "payment behaviour, say so rather than assuming.\n\n"
        "Any 'background notes' on specific companies come from your own general training "
        "knowledge, NOT a live lookup — always describe them as unverified/background context, "
        "never as confirmed fact, and never treat an unrecognised company as a bad sign.\n\n"
        "Recommendation must be one of: approve, decline, refer. As a general guide: marks "
        "close to the possible total with no reputation concerns -> approve; weak marks, or a "
        "'caution' reputation flag on a major buyer with no mitigating notes -> decline or "
        "refer; anything in between, or thin/absent salesperson notes -> refer.\n\n"
        "Return ONLY a JSON object with this exact structure, nothing else:\n"
        '{\n'
        '  "recommendation": "approve",\n'
        '  "summary": "2-5 sentence written assessment.",\n'
        '  "factors": [\n'
        '    {"factor": "short label", "detail": "1-2 sentence explanation", "impact": "positive"}\n'
        '  ]\n'
        '}\n'
        'Valid "impact" values: positive, negative, neutral. Include 3-6 factors.'
    )

    parts = [
        f"Customer: {customer.name}" + (f" ({customer.company})" if customer.company else ''),
        f"Type of business: {customer.get_type_of_business_display() or 'Unknown'}",
        f"Existing payment terms: {customer.get_payment_terms_display() or 'Not set'}",
    ]
    if customer.customer_history:
        parts.append(f"Existing customer history on this customer:\n{customer.customer_history}")

    parts.append(f"Points earned: {score_result['earned']} / {score_result['possible']}")
    for b in score_result['breakdown']:
        parts.append(f"- {b['label']}: {b['points']}/{b['max']} marks — {b['detail']}")

    listed = score_result.get('listed_signal')
    if listed:
        parts.append(
            f"Of the customer's top-tier buyers, {listed['pct_of_total_sales_from_listed']}% of that "
            f"tier's sales value comes from companies on the NSE/BSE listed reference list: "
            f"{json.dumps(listed['companies'])}"
        )

    if background_notes:
        parts.append(f"Background notes on top-tier buyers (unverified, general knowledge only): "
                      f"{json.dumps(background_notes)}")

    if quotation_signal:
        parts.append(f"In-house quotation history: {json.dumps(quotation_signal)}")

    if prior_assessment:
        parts.append(
            f"Prior assessment ({prior_assessment.created_at.date().isoformat()}): "
            f"{prior_assessment.points_earned}/{prior_assessment.points_possible} marks "
            f"({prior_assessment.risk_level}), recommendation: {prior_assessment.recommendation}.\n"
            f"Summary: {prior_assessment.summary}"
        )

    parts.append(f"Salesperson notes:\n{notes}")
    user_message = "\n\n".join(parts)

    response = chat_completion(
        model=TOGETHER_MODEL,
        messages=[{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_message}],
        max_tokens=900,
    )
    raw = response.choices[0].message.content or ''
    parsed = json.loads(raw)

    return {
        'recommendation': parsed['recommendation'] if parsed.get('recommendation') in ('approve', 'decline', 'refer') else 'refer',
        'summary': parsed.get('summary', ''),
        'factors': parsed.get('factors', []),
        'raw_response': raw,
    }


def answer_credit_question(question, customer, assessments):
    """Per-customer scoped Q&A — direct context-stuffing, not a vector-search
    RAG pipeline. The data behind one customer's assessment history is small
    and bounded (a handful of structured assessments), so chunking/embedding
    it would be pure overhead; everything relevant fits directly in context."""
    blocks = []
    for a in assessments:
        blocks.append(
            f"Assessment from {a.created_at.date().isoformat()}: "
            f"{a.points_earned}/{a.points_possible} marks, risk={a.get_risk_level_display()}, "
            f"recommendation={a.get_recommendation_display()}.\n"
            f"Summary: {a.summary}\n"
            f"Marks breakdown: {json.dumps(a.score_breakdown)}\n"
            f"Salesperson notes: {a.notes}"
        )
    context = "\n\n---\n\n".join(blocks) if blocks else "No completed assessments on file for this customer yet."

    system_prompt = (
        "You are a credit-risk assistant answering a salesperson's question about ONE specific "
        "customer, using only the assessment history provided below. If the answer isn't in the "
        "provided history, say so plainly — do not invent figures or guess."
    )
    user_message = (
        f"Customer: {customer.name}" + (f" ({customer.company})" if customer.company else '') +
        f"\n\nAssessment history:\n{context}\n\nQuestion: {question}"
    )

    response = chat_completion(
        model=TOGETHER_MODEL,
        messages=[{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_message}],
        max_tokens=600,
    )
    return response.choices[0].message.content or ''
