from django import template
from decimal import Decimal, InvalidOperation

register = template.Library()


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
