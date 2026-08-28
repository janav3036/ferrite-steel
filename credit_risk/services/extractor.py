import openpyxl


def extract_customer_financials(file_obj, filename):
    """Parses the ASSESSED CUSTOMER's OWN Tally Sales/Purchase export — the
    file is produced by the customer, not by Ferrite. 'Sales' sheet rows are
    companies the customer sold to; 'Purchase' sheet rows are companies the
    customer bought from (this is where named competitors get looked up).
    Returns {'sales': {...}|None, 'purchase': {...}|None}."""
    wb = openpyxl.load_workbook(file_obj, data_only=True)
    result = {}
    for key, sheet_name in (('sales', 'Sales'), ('purchase', 'Purchase')):
        result[key] = _extract_sheet(wb[sheet_name]) if sheet_name in wb.sheetnames else None
    return result


def _classify_columns(ws):
    """Returns (year_cols, total_count_col, total_value_col).
    The 'Total' marker can live in row1 or row2 depending on the sheet —
    check both rows for it, since either might carry it for a given column."""
    row1 = [c.value for c in ws[1]]
    row2 = [c.value for c in ws[2]]

    filled_year_label = [None] * len(row1)
    last = None
    for i, v in enumerate(row1):
        if v is not None:
            last = v
        filled_year_label[i] = last

    total_count_col = total_value_col = None
    year_cols = []
    for i, header in enumerate(row2):
        h2 = (str(header) if header else '').strip().lower()
        h1 = (str(row1[i]) if row1[i] else '').strip().lower()
        combined = h2 or h1
        if combined.startswith('total') and 'count' in combined:
            total_count_col = i
        elif combined.startswith('total') and 'taxable' in combined:
            total_value_col = i
        elif 'count' in h2:
            year_cols.append((i, 'count', filled_year_label[i]))
        elif 'taxable' in h2:
            year_cols.append((i, 'taxable_value', filled_year_label[i]))

    return year_cols, total_count_col, total_value_col


def _period_labels(year_cols):
    """Column labels don't depend on any particular row, only on year_cols'
    positions — computed once per sheet rather than once per row. Disambiguates
    a real data-quality issue seen in client exports: the same FY label (e.g.
    '23-24') repeated across two distinct column pairs."""
    labels = []
    seen = {}
    for j in range(0, len(year_cols) - 1, 2):
        _, _, year_label = year_cols[j]
        label = year_label or f'period {j // 2 + 1}'
        seen[label] = seen.get(label, 0) + 1
        labels.append(label if seen[label] == 1 else f'{label} (duplicate #{seen[label]})')
    return labels


def _is_grand_total_row(name):
    if not name:
        return False
    n = str(name).strip().lower()
    return n in ('grand total', 'total', 'grand-total')


def _row_names(ws):
    """List of (row_index, name) for every data row from row 3 onward, excluding the Grand Total row."""
    names = []
    for r in range(3, ws.max_row + 1):
        name = ws.cell(row=r, column=1).value
        if name and not _is_grand_total_row(name):
            names.append((r, str(name)))
    return names


def _grand_total(ws, total_value_col):
    if total_value_col is None:
        return 0
    # Prefer Tally's own pre-computed Grand Total row if present — more
    # reliable than re-summing, and avoids double-counting if we didn't skip it.
    for r in range(3, ws.max_row + 1):
        name = ws.cell(row=r, column=1).value
        if _is_grand_total_row(name):
            v = ws.cell(row=r, column=total_value_col + 1).value
            return v if isinstance(v, (int, float)) else 0

    total = 0
    for r in range(3, ws.max_row + 1):
        name = ws.cell(row=r, column=1).value
        if not name or _is_grand_total_row(name):
            continue
        v = ws.cell(row=r, column=total_value_col + 1).value
        if isinstance(v, (int, float)):
            total += v
    return total


def _extract_sheet(ws):
    year_cols, total_count_col, total_value_col = _classify_columns(ws)
    labels = _period_labels(year_cols)
    pairs = [(year_cols[j][0], year_cols[j + 1][0]) for j in range(0, len(year_cols) - 1, 2)]

    rows_out = []
    for r, name in _row_names(ws):
        years = []
        for label, (count_col, value_col) in zip(labels, pairs):
            years.append({
                'year': label,
                'count': ws.cell(row=r, column=count_col + 1).value,
                'taxable_value': ws.cell(row=r, column=value_col + 1).value,
            })
        total_value = ws.cell(row=r, column=total_value_col + 1).value if total_value_col is not None else None
        rows_out.append({
            'name': name,
            'years': years,
            'total_count': ws.cell(row=r, column=total_count_col + 1).value if total_count_col is not None else None,
            'total_taxable_value': total_value if isinstance(total_value, (int, float)) else 0,
        })

    return {
        'sheet': ws.title,
        'rows': rows_out,
        'row_count': len(rows_out),
        'grand_total_taxable_value': _grand_total(ws, total_value_col),
    }
