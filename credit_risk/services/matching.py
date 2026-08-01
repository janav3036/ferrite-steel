import re
import difflib

_SUFFIX_MAP = [
    (r'\bPRIVATE LIMITED\b', 'PVT LTD'),
    (r'\bPVT\.? LTD\.?\b', 'PVT LTD'),
    (r'\bLIMITED\b', 'LTD'),
    (r'\bLTD\.?\b', 'LTD'),
    (r'\b&\b', 'AND'),
]

_GENERIC_WORDS = {
    'PRIVATE', 'LIMITED', 'LTD', 'PVT', 'INDIA', 'COMPANY', 'CO',
    'ENTERPRISES', 'INDUSTRIES', 'CORPORATION', 'CORP', 'THE', 'AND',
}


def _core(normalized_name):
    tokens = [t for t in normalized_name.split() if t not in _GENERIC_WORDS]
    return ' '.join(tokens) if tokens else normalized_name

AUTO_ACCEPT_CUTOFF = 0.75
MIN_NORMALIZED_LEN = 6

def normalize(name):
    s = (name or '').upper().strip()
    s = re.sub(r'[.,]', '', s)
    s = re.sub(r'\s+', ' ', s)
    for pattern, repl in _SUFFIX_MAP:
        s = re.sub(pattern, repl, s)
    return s.strip()

def find_best_match(target_names, candidate_names):
    """
    target_names: e.g. [customer.name, customer.company]
    candidate_names: raw names read from the sheet's first column
    Returns {'matched_name', 'match_type', 'score', 'alternatives'} or None.
    """
    targets = [normalize(t) for t in target_names if t and len(normalize(t)) >= MIN_NORMALIZED_LEN]
    if not targets or not candidate_names:
        return None

    norm_to_raw = {}
    for raw in candidate_names:
        norm_to_raw.setdefault(normalize(raw), raw)
    norm_candidates = list(norm_to_raw.keys())

    for t in targets:
        if t in norm_to_raw:
            return {'matched_name': norm_to_raw[t], 'match_type': 'exact', 'score': 1.0, 'alternatives': []}

    MIN_CORE_LEN_FOR_FUZZY = 6

    scored = []
    for t in targets:
        ct = _core(t)
        for nc in norm_candidates:
            cnc = _core(nc)
            if len(ct) < MIN_CORE_LEN_FOR_FUZZY or len(cnc) < MIN_CORE_LEN_FOR_FUZZY:
                ratio = 1.0 if ct == cnc else 0.0
            else:
                ratio = difflib.SequenceMatcher(None, ct, cnc).ratio()
            if ratio >= 0.5:
                scored.append((ratio, norm_to_raw[nc]))
                
    if not scored:
        return None
    scored.sort(key=lambda x: -x[0])
    best_score, best_name = scored[0]
    if best_score < AUTO_ACCEPT_CUTOFF:
        return None

    alternatives = [name for score, name in scored[1:6] if score >= best_score - 0.1 and name != best_name]
    return {
        'matched_name': best_name, 'match_type': 'fuzzy',
        'score': round(best_score, 3), 'alternatives': alternatives
    }