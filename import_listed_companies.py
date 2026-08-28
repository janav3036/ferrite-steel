"""
One-time (re-runnable) import: seeds credit_risk.ListedCompany from NSE's
public equity list (extra_data/nse_equity_list.csv, ~2,559 companies, sourced
from https://nsearchives.nseindia.com/content/equities/EQUITY_L.csv).

BSE's list isn't included yet — their bulk API needs session auth I haven't
chased down. If Janav sources a BSE CSV later (columns: just needs a company
name column), run:
    python import_listed_companies.py extra_data/bse_equity_list.csv bse

Usage:
    python import_listed_companies.py                                  # NSE only, default path
    python import_listed_companies.py path/to/file.csv nse|bse|both
"""
import csv
import os
import sys

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ferite_steel.settings')
django.setup()

from credit_risk.models import ListedCompany  # noqa: E402

DEFAULT_PATH = os.path.join('extra_data', 'nse_equity_list.csv')


def import_csv(path, exchange):
    created = updated = 0
    with open(path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        name_col = next((c for c in reader.fieldnames if 'name' in c.lower()), None)
        if not name_col:
            raise SystemExit(f"Couldn't find a name column in {path}. Columns found: {reader.fieldnames}")
        for row in reader:
            name = (row.get(name_col) or '').strip()
            if not name:
                continue
            obj, was_created = ListedCompany.objects.get_or_create(
                name=name, defaults={'exchange': exchange},
            )
            if was_created:
                created += 1
            elif obj.exchange != exchange and obj.exchange != 'both':
                obj.exchange = 'both'
                obj.save(update_fields=['exchange'])
                updated += 1
    print(f'{path}: {created} created, {updated} updated to dual-listed.')


if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_PATH
    exchange = sys.argv[2] if len(sys.argv) > 2 else 'nse'
    if exchange not in ('nse', 'bse', 'both'):
        raise SystemExit("exchange must be 'nse', 'bse', or 'both'")
    import_csv(path, exchange)
    print(f'Total ListedCompany rows: {ListedCompany.objects.count()}')
