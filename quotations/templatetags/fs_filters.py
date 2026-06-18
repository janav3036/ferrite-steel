from django import template
from decimal import Decimal, InvalidOperation

register = template.Library()


@register.filter
def inr_words(value):
    """Convert a Decimal/number to Indian-English amount words, e.g. ₹1,36,144.00 → One Lakh Thirty-Six Thousand One Hundred Forty-Four Only."""
    try:
        val = Decimal(str(value))
        rupees = int(val)
        paise  = round((val - rupees) * 100)
    except (InvalidOperation, TypeError, ValueError):
        return ''

    _ones = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine',
             'Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen',
             'Seventeen', 'Eighteen', 'Nineteen']
    _tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']

    def _two(n):
        if n == 0:  return ''
        if n < 20:  return _ones[n]
        return _tens[n // 10] + (' ' + _ones[n % 10] if n % 10 else '')

    def _three(n):
        if n == 0:  return ''
        h, r = divmod(n, 100)
        s = (_ones[h] + ' Hundred') if h else ''
        t = _two(r)
        return (s + ' ' + t).strip() if (s and t) else (s or t)

    def _to_words(n):
        if n == 0: return 'Zero'
        parts = []
        crore, n = divmod(n, 10_000_000)
        lakh,  n = divmod(n, 100_000)
        thous, n = divmod(n, 1_000)
        if crore: parts.append(_three(crore) + ' Crore')
        if lakh:  parts.append(_two(lakh)    + ' Lakh')
        if thous: parts.append(_two(thous)   + ' Thousand')
        if n:     parts.append(_three(n))
        return ' '.join(parts)

    result = _to_words(rupees) + ' Rupees'
    if paise:
        result += ' and ' + _two(int(paise)) + ' Paise'
    return result + ' Only'


@register.filter
def inr(value):
    """Format a number using Indian grouping: ₹50,00,000.00"""
    try:
        val = Decimal(str(value))
        negative = val < 0
        val = abs(val)
        int_part = str(int(val))
        dec_part = f'{val % 1:.2f}'[1:]  # '.xx'

        if len(int_part) > 3:
            last_three = int_part[-3:]
            rest = int_part[:-3]
            groups = []
            while len(rest) > 2:
                groups.append(rest[-2:])
                rest = rest[:-2]
            if rest:
                groups.append(rest)
            groups.reverse()
            formatted = ','.join(groups) + ',' + last_three
        else:
            formatted = int_part

        result = f'₹{formatted}{dec_part}'
        return f'-{result}' if negative else result
    except (InvalidOperation, TypeError, ValueError):
        return value
