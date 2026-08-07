from quotations.models import Lead, Quotation

MIN_QUOTATIONS_FOR_SIGNAL = 20


def build_quotation_signal(customer):
    """In-house quotation history for this customer, as an extra credit signal.

    Returns None below MIN_QUOTATIONS_FOR_SIGNAL — with only a handful of
    quotations, a win rate or average order value is not a reliable signal
    (a single early loss would read as a 0% win rate) and would mislead the
    LLM more than it would help. Only counts root quotations (one per deal;
    revisions share the root's outcome, see Quotation.outcome docs) to avoid
    inflating the count with -v2/-v3 revisions of the same deal.
    """
    leads = Lead.objects.none()
    if customer.email:
        leads = Lead.objects.filter(customer_email__iexact=customer.email)
    if customer.name:
        by_name = Lead.objects.filter(customer_name__iexact=customer.name, company__iexact=customer.company)
        leads = leads | by_name
    leads = leads.distinct()

    deals = Quotation.objects.filter(lead__in=leads, parent_quotation__isnull=True)
    total = deals.count()
    if total < MIN_QUOTATIONS_FOR_SIGNAL:
        return None

    won = deals.filter(outcome='win').count()
    lost = deals.filter(outcome='loss').count()
    decided = won + lost
    most_recent = deals.order_by('-created_at').first()

    return {
        'total_quotations': total,
        'won': won,
        'lost': lost,
        'win_rate_pct': round(won / decided * 100, 1) if decided else None,
        'most_recent_date': most_recent.created_at.date().isoformat() if most_recent else None,
    }
