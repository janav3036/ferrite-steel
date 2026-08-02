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
            'Look up rate and stock for a steel product by item number, product name, or HSN code. '
            'Returns data from the product catalog. Always returns found: true/false.'
        ),
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': 'Item number, product name, or HSN code to search for (e.g. "ISAM00012", "Angle 100X100X10", "72141000")',
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
        Q(item_no__icontains=query) | Q(product_name__icontains=query) | Q(hsn_code__icontains=query)
    ).select_related('base_product').distinct()

    data = [
        {
            'item_no': p.item_no,
            'product_name': p.product_name,
            'hsn_code': p.hsn_code,
            'unit': p.get_unit_display(),
            'quantity': str(p.quantity),
            'rate': str(p.effective_rate),
        }
        for p in results
    ]

    return {
        'found': bool(data),
        'results': data,
    }
