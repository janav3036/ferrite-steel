"""Deterministic point-scoring — the client's fixed marking scheme, computed
in Python and never left to the LLM to derive (same principle as the old
rank/streak-flag computation this replaces). See services/llm.py for how
these marks get handed to the model as labeled facts, not raw numbers."""
import math

from .matching import find_best_match

GENERIC_TIERS = {'good', 'mid', 'bad'}

# Client's marking scheme, scaled proportionally if CreditScoringConfig
# overrides the category max (e.g. competitor_max=5 instead of 3).
BASE_COMPETITOR_TABLE = {
    ('good', 'streak'): 3.0,
    ('good', 'new'): 2.5,
    ('mid', 'streak'): 2.0,
    ('mid', 'new'): 1.5,
    ('bad', 'streak'): 1.0,
    ('bad', 'new'): 0.5,
    ('bad', 'none'): 0.5,
}
BASE_COMPETITOR_MAX = 3.0

TOP_TIER_FRACTION = 0.10
CONCENTRATION_DOMINANT_PCT = 80.0
RETENTION_OVERLAP_THRESHOLD = 0.2  # some repeat customers between consecutive years
CRORE = 10_000_000


class Weights:
    def __init__(self, competitor_max, concentration_max, turnover_max,
                 sales_vs_purchase_max, sales_vs_purchase_active):
        self.competitor_max = competitor_max
        self.concentration_max = concentration_max
        self.turnover_max = turnover_max
        self.sales_vs_purchase_max = sales_vs_purchase_max
        self.sales_vs_purchase_active = sales_vs_purchase_active


def resolve_weights(overrides=None):
    """overrides: optional dict (CreditAssessment.weight_overrides shape) that
    wins over the global CreditScoringConfig singleton for this one run."""
    from .. import models as m
    cfg = m.CreditScoringConfig.current()
    overrides = overrides or {}
    return Weights(
        competitor_max=float(overrides.get('competitor_max', cfg.competitor_max)),
        concentration_max=float(overrides.get('concentration_max', cfg.concentration_max)),
        turnover_max=float(overrides.get('turnover_max', cfg.turnover_max)),
        sales_vs_purchase_max=float(overrides.get('sales_vs_purchase_max', cfg.sales_vs_purchase_max)),
        sales_vs_purchase_active=bool(overrides.get('sales_vs_purchase_active', cfg.sales_vs_purchase_active)),
    )


def parse_competitors(raw_text):
    """Customer.competitors, one per line as 'Name - tier' (tier is client-set,
    hardcoded — never inferred). Unlabelled/unrecognised lines default to 'mid'."""
    out = []
    for line in (raw_text or '').splitlines():
        line = line.strip()
        if not line:
            continue
        name, tier = line, 'mid'
        if '-' in line:
            candidate_name, _, candidate_tier = line.rpartition('-')
            candidate_tier = candidate_tier.strip().lower()
            if candidate_name.strip() and candidate_tier in GENERIC_TIERS:
                name, tier = candidate_name.strip(), candidate_tier
        out.append({'name': name, 'tier': tier})
    return out


def _streak_category(years):
    """years: chronologically ordered [{'year','count','taxable_value'}, ...].
    'streak' = active every period on file. 'new' = only appeared in the most
    recent 1-2 periods, continuously since first appearing. Anything else
    (a mid-file gap, or activity that stopped before the latest period) = 'none'."""
    active = [bool(y.get('count')) for y in years]
    n = len(active)
    if n == 0 or not any(active):
        return 'none'
    if all(active):
        return 'streak'
    first_idx = next(i for i, a in enumerate(active) if a)
    last_idx = max(i for i, a in enumerate(active) if a)
    continuous_to_present = last_idx == n - 1 and all(active[first_idx:])
    if continuous_to_present and (n - first_idx) <= 2:
        return 'new'
    return 'none'


def competitor_marks(competitors_raw, purchase_rows, weights):
    max_pts = weights.competitor_max
    competitors = parse_competitors(competitors_raw)
    if not competitors or not purchase_rows:
        return {'points': 0.0, 'max': max_pts, 'matches': [], 'best': None}

    row_names = [r['name'] for r in purchase_rows]
    rows_by_name = {r['name']: r for r in purchase_rows}
    matches = []
    for comp in competitors:
        match = find_best_match([comp['name']], row_names)
        if not match:
            continue
        row = rows_by_name[match['matched_name']]
        streak = _streak_category(row['years'])
        base_points = BASE_COMPETITOR_TABLE.get((comp['tier'], streak), 0.0)
        scaled = round(base_points / BASE_COMPETITOR_MAX * max_pts, 1)
        matches.append({
            'competitor': comp['name'], 'tier': comp['tier'], 'matched_row': match['matched_name'],
            'match_type': match['match_type'], 'streak': streak, 'points': scaled,
        })

    if not matches:
        return {'points': 0.0, 'max': max_pts, 'matches': [], 'best': None}

    best = max(matches, key=lambda m: m['points'])
    return {'points': best['points'], 'max': max_pts, 'matches': matches, 'best': best}


def _row_value(row):
    v = row.get('total_taxable_value') or 0
    return v if isinstance(v, (int, float)) else 0


def _year_over_year_retention(rows):
    """Average Jaccard overlap of the active-customer set between consecutive years."""
    if not rows or not rows[0].get('years'):
        return None
    n_years = len(rows[0]['years'])
    if n_years < 2:
        return None
    year_sets = [
        {r['name'] for r in rows if r['years'][i].get('count')}
        for i in range(n_years)
    ]
    overlaps = []
    for a, b in zip(year_sets, year_sets[1:]):
        union = a | b
        if union:
            overlaps.append(len(a & b) / len(union))
    return sum(overlaps) / len(overlaps) if overlaps else None


def concentration_marks(sales_rows, weights):
    max_pts = weights.concentration_max
    if not sales_rows:
        return {'points': 0.0, 'max': max_pts, 'top_n': 0, 'top_pct': None,
                'top_rows': [], 'detail': 'No sales rows found in the uploaded file.'}

    sorted_rows = sorted(sales_rows, key=_row_value, reverse=True)
    grand_total = sum(_row_value(r) for r in sorted_rows)
    top_n = max(1, math.ceil(len(sorted_rows) * TOP_TIER_FRACTION))
    top_rows = sorted_rows[:top_n]
    top_total = sum(_row_value(r) for r in top_rows)
    top_pct = (top_total / grand_total * 100) if grand_total else 0.0

    if top_pct >= CONCENTRATION_DOMINANT_PCT:
        points = max_pts
        detail = f"Top {top_n} customers ({round(top_pct)}% of sales) dominate revenue."
    else:
        overlap = _year_over_year_retention(sorted_rows)
        if overlap is not None and overlap >= RETENTION_OVERLAP_THRESHOLD:
            points = round(max_pts / 2, 1)
            detail = f"Customer base varies year to year but retains repeat buyers ({round(overlap * 100)}% overlap)."
        else:
            points = 0.0
            detail = "Customers are almost entirely new each year — little repeat business."

    return {
        'points': points, 'max': max_pts, 'top_n': top_n, 'top_pct': round(top_pct, 1),
        'top_rows': top_rows, 'detail': detail,
    }


def turnover_marks(sales_grand_total, weights):
    max_pts = weights.turnover_max
    total = sales_grand_total or 0
    if total >= 100 * CRORE:
        ratio = 1.0
    elif total >= 30 * CRORE:
        ratio = 0.5
    else:
        ratio = 0.25
    return {'points': round(max_pts * ratio, 1), 'max': max_pts, 'grand_total': total}


def sales_vs_purchase_marks(sales_grand_total, purchase_grand_total, weights):
    """Built per spec, but parked — CreditScoringConfig.sales_vs_purchase_active
    gates whether it counts toward points_possible at all."""
    if not weights.sales_vs_purchase_active:
        return None
    max_pts = weights.sales_vs_purchase_max
    purchase = purchase_grand_total or 0
    sales = sales_grand_total or 0
    points = max_pts if (purchase and sales > purchase * 1.25) else 0.0
    return {'points': points, 'max': max_pts, 'sales': sales, 'purchase': purchase}


def listed_company_signal(top_rows, grand_total):
    """Informational only — not a scored mark. Matches the customer's own
    top-tier buyers against the ListedCompany reference table."""
    from .. import models as m
    listed_names = list(m.ListedCompany.objects.values_list('name', flat=True))
    if not listed_names or not top_rows:
        return None

    flagged = []
    listed_value = 0
    for row in top_rows:
        match = find_best_match([row['name']], listed_names)
        is_listed = bool(match)
        if is_listed:
            listed_value += _row_value(row)
        flagged.append({'name': row['name'], 'listed': is_listed})

    pct_of_total = round(listed_value / grand_total * 100, 1) if grand_total else None
    return {'companies': flagged, 'pct_of_total_sales_from_listed': pct_of_total}


def compute_score_breakdown(sales, purchase, competitors_raw, weights):
    sales_rows = sales['rows'] if sales else []
    purchase_rows = purchase['rows'] if purchase else []
    sales_grand_total = sales['grand_total_taxable_value'] if sales else 0
    purchase_grand_total = purchase['grand_total_taxable_value'] if purchase else 0

    comp = competitor_marks(competitors_raw, purchase_rows, weights)
    conc = concentration_marks(sales_rows, weights)
    turn = turnover_marks(sales_grand_total, weights)
    svp = sales_vs_purchase_marks(sales_grand_total, purchase_grand_total, weights)
    listed = listed_company_signal(conc['top_rows'], sales_grand_total) if conc['top_rows'] else None

    breakdown = [
        {'category': 'competitors', 'label': 'Competitor Streak', 'points': comp['points'], 'max': comp['max'],
         'detail': _competitor_detail(comp)},
        {'category': 'concentration', 'label': "Customer's-Customer Concentration", 'points': conc['points'], 'max': conc['max'],
         'detail': conc['detail']},
        {'category': 'turnover', 'label': 'Sales Turnover', 'points': turn['points'], 'max': turn['max'],
         'detail': f"Customer's total sales turnover on file: {turn['grand_total']:,.0f}"},
    ]
    if svp is not None:
        breakdown.append({
            'category': 'sales_vs_purchase', 'label': 'Sales vs Purchases', 'points': svp['points'], 'max': svp['max'],
            'detail': f"Sales {svp['sales']:,.0f} vs Purchases {svp['purchase']:,.0f}",
        })

    earned = round(sum(b['points'] for b in breakdown), 1)
    possible = round(sum(b['max'] for b in breakdown), 1)

    return {
        'breakdown': breakdown,
        'earned': earned,
        'possible': possible,
        'top_tier_names': [r['name'] for r in conc['top_rows']],
        'listed_signal': listed,
        'competitor_matches': comp['matches'],
    }


def _competitor_detail(comp):
    if not comp['best']:
        return "None of the listed competitors were found buying from this customer."
    b = comp['best']
    return f"{b['competitor']} ({b['tier']} competitor) has a '{b['streak']}' buying relationship with this customer."
