"""
Tool definition: look up a product in the master pricing sheet.
The LLM calls this tool during quotation generation.
"""
from quotations.models import PricingEntry


TOOL_DEFINITION = {
    'type': 'function',
    'function': {
        'name': 'lookup_pricing',
        'description': (
            'Look up the base price and unit for a steel product by name or code. '
            'Returns pricing data from the master pricing sheet.'
        ),
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {
                    'type': 'string',
                    'description': 'Product name or product code to search for',
                },
            },
            'required': ['query'],
        },
    },
}


def lookup_pricing(query: str) -> dict:
    """
    Called when the LLM invokes the lookup_pricing tool.
    Returns matching products from PricingEntry, or an empty list if none found.
    """
    results = PricingEntry.objects.filter(
        is_active=True,
    ).filter(
        product_name__icontains=query,
    ) | PricingEntry.objects.filter(
        is_active=True,
        product_code__icontains=query,
    )

    return {
        'results': [
            {
                'product_code': p.product_code,
                'product_name': p.product_name,
                'unit': p.unit,
                'base_price': str(p.base_price),
                'min_quantity': str(p.min_quantity),
            }
            for p in results.distinct()
        ]
    }
