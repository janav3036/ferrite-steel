"""
Tool definition: look up a product in the master product catalog.
The LLM calls this tool during quotation generation.
"""
from django.db.models import Q
from database.models import Product


TOOL_DEFINITION = {
    'type': 'function',
    'function': {
        'name': 'lookup_pricing',
        'description': (
            'Look up rate and stock for a steel product by size, sub-type, or HSN code. '
            'Returns data from the product catalog. Always returns found: true/false.'
        ),
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': 'Size, sub-type, or HSN code to search for (e.g. "12mm", "Angle", "72141000")',
                },
            },
            'required': ['query'],
        },
    },
}


def lookup_pricing(query: str) -> dict:
    """
    Called when the LLM invokes the lookup_pricing tool.
    Returns found: bool plus matching products from the catalog.
    """
    results = Product.objects.filter(
        is_active=True,
    ).filter(
        Q(size__icontains=query) | Q(hsn_code__icontains=query) | Q(sub_type__icontains=query)
    ).distinct()

    data = [
        {
            'hsn_code': p.hsn_code,
            'make': p.get_make_display(),
            'sub_type': p.get_sub_type_display(),
            'size': p.size,
            'length': p.length or None,
            'pieces': p.pieces,
            'grade': p.grade,
            'location': p.location,
            'quantity': str(p.quantity),
            'rate': str(p.rate),
        }
        for p in results
    ]

    return {
        'found': bool(data),
        'results': data,
    }
