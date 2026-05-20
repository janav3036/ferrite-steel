"""
One-time import script: Business Partner ALL.xlsx → database.Customer

Filters to Group Name = 'Sundry Debtors' (actual customers only).
Groups by BP Code. First address row = billing, second = shipping.
Uses update_or_create on customer_code — safe to re-run.

Run from project root:
    source .venv/bin/activate
    python import_business_partners.py
"""

import os
import sys
import django
from collections import defaultdict
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ferite_steel.settings')
django.setup()

import openpyxl
from database.models import Customer

EXCEL_PATH = 'Business Partner ALL.xlsx'
TARGET_GROUP = 'Sundry Debtors'

# Column indices (0-based)
COL_BP_CODE       = 1
COL_BP_NAME       = 2
COL_GROUP_NAME    = 5
COL_GST           = 6
COL_MSME          = 7
COL_STREET        = 9
COL_ZIP           = 10
COL_CITY          = 11
COL_PHONE         = 14
COL_EMAIL         = 15
COL_BUILDING      = 16
COL_TAX_PAN       = 17
COL_BILLING_PAN   = 18
COL_BIZ_TYPE      = 20
COL_ACTIVE        = 21
COL_CREATED       = 22


def clean(val):
    if val is None:
        return ''
    s = str(val).strip()
    return '' if s in ('None', 'N/A', 'NA', 'na', '-No Sales Employee-') else s


def parse_date(val):
    s = clean(val)
    if not s:
        return None
    try:
        return datetime.strptime(s, '%d-%m-%Y').date()
    except ValueError:
        return None


def build_address(building, street, city, pincode):
    parts = [clean(v) for v in [building, street, city, pincode]]
    return ', '.join(p for p in parts if p)


def is_likely_msme(val):
    """Return False for phone numbers that ended up in the MSME column."""
    if not val:
        return False
    # Real MSME/Udhyan numbers contain letters; pure-digit strings are phone numbers
    return not val.isdigit()


def main():
    print(f'Loading {EXCEL_PATH} ...')
    wb = openpyxl.load_workbook(EXCEL_PATH, read_only=True, data_only=True)
    ws = wb.active
    all_rows = list(ws.iter_rows(values_only=True))
    print(f'Total rows (incl. header): {len(all_rows)}')

    # Group rows by BP code, keeping only Sundry Debtors
    bp_groups = defaultdict(list)
    for r in all_rows[1:]:
        if r[COL_GROUP_NAME] == TARGET_GROUP and r[COL_BP_CODE]:
            bp_groups[r[COL_BP_CODE]].append(r)

    print(f'Unique BP codes in Sundry Debtors: {len(bp_groups)}')

    created_count = 0
    updated_count = 0

    for bp_code, addr_rows in bp_groups.items():
        first = addr_rows[0]
        second = addr_rows[1] if len(addr_rows) > 1 else None

        billing_address  = build_address(first[COL_BUILDING], first[COL_STREET],
                                         first[COL_CITY], first[COL_ZIP])
        shipping_address = (build_address(second[COL_BUILDING], second[COL_STREET],
                                          second[COL_CITY], second[COL_ZIP])
                            if second else '')

        # PAN: prefer Billing PAN column, fall back to Tax info PAN
        pan = clean(first[COL_BILLING_PAN]) or clean(first[COL_TAX_PAN])

        msme_raw = clean(first[COL_MSME])
        msme = msme_raw if is_likely_msme(msme_raw) else ''

        biz_type = clean(first[COL_BIZ_TYPE])
        if biz_type not in ('C', 'I', 'G'):
            biz_type = ''

        obj, created = Customer.objects.update_or_create(
            customer_code=bp_code,
            defaults={
                'name':             clean(first[COL_BP_NAME]) or bp_code,
                'company':          '',       # BP Name is the entity name — stored in `name`
                'phone':            clean(first[COL_PHONE])[:30],
                'email':            clean(first[COL_EMAIL]),
                'gst_number':       clean(first[COL_GST]),
                'pan_number':       pan,
                'msme_number':      msme,
                'city':             clean(first[COL_CITY]),
                'pincode':          clean(first[COL_ZIP])[:10],
                'billing_address':  billing_address,
                'shipping_address': shipping_address,
                'type_of_business': biz_type,
                'is_active':        clean(first[COL_ACTIVE]) == 'Y',
                'sap_created_at':   parse_date(first[COL_CREATED]),
            },
        )

        if created:
            created_count += 1
        else:
            updated_count += 1

    print(f'\nDone.')
    print(f'  Created : {created_count}')
    print(f'  Updated : {updated_count}')
    print(f'  Total   : {created_count + updated_count}')


if __name__ == '__main__':
    main()
