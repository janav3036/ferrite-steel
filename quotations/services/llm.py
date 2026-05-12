"""
Wrapper for together.ai LLM calls with tool use / function calling.
All views must call this service layer — never call together.ai directly.
"""
import os


TOGETHER_API_KEY = os.environ.get('TOGETHER_API_KEY', '')
TOGETHER_MODEL = os.environ.get('TOGETHER_MODEL', 'meta-llama/Llama-3.3-70B-Instruct-Turbo')


def generate_quotation_draft(lead, entity_notes: str = '') -> dict:
    """
    Generate a quotation draft using the lead's enquiry text, lead notes, and
    customer/broker notes. Calls together.ai with lookup_pricing tool.

    Arguments:
        lead         — Lead model instance (uses lead.raw_text, lead.notes)
        entity_notes — notes from the related Customer or Broker record

    Returns a dict matching QuotationEditForm + LineItemFormSet fields:
    {
        "payment_terms": "Advance",
        "delivery_address": "",
        "transport_extra": 0,
        "sgst_percent": 9,
        "cgst_percent": 9,
        "notes": "",
        "valid_until": "YYYY-MM-DD",   # or null
        "line_items": [
            {
                "product_name": "TMT Bars",
                "make": "TATA",
                "length": null,
                "pcs": null,
                "quantity": 5.5,
                "unit_price": 55000,
                "notes": ""
            }
        ]
    }

    Stub — wire together.ai client here in Phase 2 once API key is available.
    """
    raise NotImplementedError('LLM service not yet implemented — Phase 2 in progress.')
