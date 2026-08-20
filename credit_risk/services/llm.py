import json

from ferite_steel.ai import chat_completion

TOGETHER_MODEL = 'meta-llama/Llama-3.3-70B-Instruct-Turbo'

RISK_BANDS = [(8, 10, 'low'), (4, 7, 'medium'), (1, 3, 'high')]


def _risk_level_for_score(score):
    for lo, hi, level in RISK_BANDS:
        if lo <= score <= hi:
            return level
    return 'high'


def assess_credit(customer, notes, trading_history, prior_assessment=None, quotation_signal=None):
    system_prompt = (
        "You are a credit-risk assistant for an iron and steel distribution company in India, "
        "helping a salesperson decide whether to extend trade credit to a customer.\n\n"
        "You will be given: (1) basic customer profile fields, (2) trading history extracted "
        "from this company's own Tally accounting export, and (3) free-text notes from the "
        "salesperson.\n\n"
        "IMPORTANT LIMITATION: the trading history data contains ONLY transaction Count and "
        "Taxable Value per financial year — it has NO ageing, NO outstanding-balance, and NO "
        "payment-delay or default information. Treat it only as a signal of relationship depth, "
        "order consistency, and trend (growing/shrinking/stopped) — NOT as direct evidence of "
        "payment behaviour. For actual payment behaviour (delays, disputes, bounced cheques, "
        "etc.) rely on the salesperson's notes; if the notes don't mention payment behaviour, "
        "say so explicitly rather than assuming.\n\n"
        "Sales-sheet data = this company's own historical sales TO the customer — the most "
        "relevant ledger for assessing them as a buyer. Purchase-sheet data = money this "
        "company paid THIS COUNTERPARTY as a vendor/supplier — it does not reflect their "
        "creditworthiness as a buyer and should be treated as minor supplementary context only "
        "(e.g. a reciprocal business relationship), never as a primary signal.\n\n"
        "COMPANY-WIDE CONTEXT: you will be given a 'holding stock' signal comparing the whole "
        "company's total Sales vs total Purchases across ALL customers/vendors in the uploaded "
        "file. This is NOT specific to this customer — it is background market/business "
        "condition context only.\n\n"
        "VENDOR RANK & STREAK FLAGS: if this customer is also one of the company's top-20 "
        "vendors by purchase value, you'll be told their rank, and any 'streak flags' — a "
        "'trailing_falloff' flag (weight 2, meaning: the vendor relationship was active and "
        "recently went quiet — this may indicate stuck credit with that vendor and should be "
        "weighted twice as heavily as a mid_gap flag) or a 'mid_gap' flag (weight 1, an old gap "
        "that later recovered). Always mention any flags in your factors, weighted accordingly, "
        "unless the notes provide a benign explanation.\n\n"
        "If no match was found for this customer in the Sales sheet, Purchase sheet, or both, "
        "this will be explicitly marked. In that case you MUST state clearly in the summary "
        "that no trading history was found for this customer in the uploaded file, and rely on "
        "the notes alone — do not imply a complete assessment when evidence is partial or "
        "absent, and lean toward a lower score / 'refer' recommendation when both trading "
        "history and notes offer limited signal.\n\n"
        "IN-HOUSE QUOTATION HISTORY: if provided, this is the customer's own quotation record "
        "from this company's CRM (total quotations, win/loss count, most recent date) — a "
        "direct, steel-business-relevant signal, more specific than the Tally export. Treat it "
        "as a meaningful factor when present. It is only included when the customer has enough "
        "quotations on file for the numbers to be reliable, so if it's absent, do not assume "
        "the customer has no relationship with the company — just don't mention it.\n\n"
        "PRIOR ASSESSMENT: if provided, this is the most recent previous assessment for this "
        "same customer. Use it as a checkpoint to comment on whether risk has changed since "
        "then (improved/worsened/unchanged) in your summary — but do not anchor to the old "
        "score. Re-derive your score fresh from the current evidence; the prior score is context, "
        "not a starting point.\n\n"
        "Score the customer 1-10 (10 = excellent / lowest risk, 1 = very poor / highest risk).\n"
        "Score bands: 8-10 = low risk, 4-7 = medium risk, 1-3 = high risk.\n"
        "Recommendation must be one of: approve, decline, refer.\n"
        "Return ONLY a JSON object with this exact structure, nothing else:\n"
        '{\n'
        '  "score": 7,\n'
        '  "recommendation": "approve",\n'
        '  "summary": "2-5 sentence written assessment.",\n'
        '  "factors": [\n'
        '    {"factor": "short label", "detail": "1-2 sentence explanation", "impact": "positive"}\n'
        '  ]\n'
        '}\n'
        'Valid "impact" values: positive, negative, neutral. Include 3-6 factors.'
    )

    sales = trading_history.get('sales') if trading_history else None
    purchase = trading_history.get('purchase') if trading_history else None
    company_context = trading_history.get('company_context') if trading_history else None
    no_history_found = sales is None and purchase is None

    parts = [
        f"Customer: {customer.name}" + (f" ({customer.company})" if customer.company else ''),
        f"Type of business: {customer.get_type_of_business_display() or 'Unknown'}",
        f"Existing payment terms: {customer.get_payment_terms_display() or 'Not set'}",
    ]
    if customer.notes:
        parts.append(f"Existing CRM notes on this customer:\n{customer.notes}")
    if company_context:
        parts.append(f"Company-wide context (not customer-specific): {json.dumps(company_context)}")
    if no_history_found:
        parts.append("TRADING HISTORY: No match found for this customer in either the Sales or "
                      "Purchase sheet of the uploaded file. Assess based on notes only and say so.")
    else:
        parts.append(f"Sales-sheet match: {json.dumps(sales) if sales else 'No match found in Sales sheet.'}")
        parts.append(f"Purchase-sheet match: {json.dumps(purchase) if purchase else 'No match found in Purchase sheet.'}")
    if quotation_signal:
        parts.append(f"In-house quotation history: {json.dumps(quotation_signal)}")
    if prior_assessment:
        parts.append(
            f"Prior assessment ({prior_assessment.created_at.date().isoformat()}): "
            f"score {prior_assessment.score}/10 ({prior_assessment.risk_level}), "
            f"recommendation: {prior_assessment.recommendation}.\nSummary: {prior_assessment.summary}"
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

    score = max(1, min(10, int(parsed['score'])))
    return {
        'score': score,
        'risk_level': _risk_level_for_score(score),
        'recommendation': parsed['recommendation'] if parsed.get('recommendation') in ('approve', 'decline', 'refer') else 'refer',
        'summary': parsed.get('summary', ''),
        'factors': parsed.get('factors', []),
        'raw_response': raw,
    }


def compute_data_confidence(trading_history, notes, quotation_signal):
    """How much the inputs behind a given score are actually worth trusting —
    computed the same way as risk_level: deterministically in Python, never
    left to the LLM to self-report, so it can't inflate its own confidence."""
    sales = trading_history.get('sales') if trading_history else None
    purchase = trading_history.get('purchase') if trading_history else None
    exact_match = any(m and m.get('match_type') == 'exact' for m in (sales, purchase))
    any_match = bool(sales or purchase)
    notes_substantial = len((notes or '').strip()) >= 40

    points = 0
    if any_match:
        points += 2 if exact_match else 1
    if notes_substantial:
        points += 1
    if quotation_signal:
        points += 1

    if points >= 3:
        return 'high'
    if points >= 1:
        return 'medium'
    return 'low'