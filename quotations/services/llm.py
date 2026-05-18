"""
Wrapper for together.ai LLM calls with tool use / function calling.
All views must call this service layer — never call together.ai directly.
"""
import json
from ferite_steel.ai import together_client
from .tools.pricing import lookup_pricing, TOOL_DEFINITION as PRICING_TOOL

TOGETHER_MODEL = 'meta-llama/Llama-3.3-70B-Instruct-Turbo'


def _build_keyword_context() -> str:
    from quotations.models import ProductKeyword
    keywords = ProductKeyword.objects.filter(is_active=True).values_list('keyword', 'maps_to')
    if not keywords:
        return ''
    lines = '\n'.join(f'  "{kw}" means "{mt}"' for kw, mt in keywords)
    return f'Client terminology guide (local/trade names to use when calling lookup_pricing):\n{lines}'


def classify_message(text: str) -> bool:
    """
    Returns True if text is a product inquiry for iron/steel goods, False otherwise.
    Call this before creating a Lead from any inbound message (email, WhatsApp).
    """
    response = together_client.chat.completions.create(
        model=TOGETHER_MODEL,
        messages=[
            {
                'role': 'system',
                'content': (
                    'You are a classifier for an iron and steel distribution company in India. '
                    'Decide whether the message below is a product inquiry — i.e. the sender '
                    'is asking about steel or iron products, prices, availability, or requesting '
                    'a quotation. Reply with exactly one word: YES or NO.'
                ),
            },
            {'role': 'user', 'content': text},
        ],
        max_tokens=5,
    )
    answer = (response.choices[0].message.content or '').strip().upper()
    return answer.startswith('YES')


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

    """

    keyword_context = _build_keyword_context()
    system_prompt = (
        "You are a quotation assistant for an iron and steel distribution company in India. "
        "Given a customer enquiry, use the lookup_pricing tool to find rates for the requested products. "
        "When calling lookup_pricing, use short search terms — search by size (e.g. '12mm') or product type (e.g. 'TMT') separately, not the full description. "
        "IMPORTANT: Ignore any prices or rates mentioned in the enquiry text — always use lookup_pricing to get the correct rate from the catalog. "
        "IMPORTANT: The enquiry may come from an email reply chain. Focus only on the new request at the top — ignore any previously quoted or repeated content below it. "
        + (f"\n{keyword_context}\n" if keyword_context else "")
        + "Quantities may be in tonnes (T) or kilograms (KG) — 1 tonne = 1000 KG. "
        "Preserve the unit as stated by the customer. Rates in the catalog are per tonne (₹/T); "
        "if the customer specifies KG, set uom='kg' and keep quantity in KG — do not convert. "
        "Then return a JSON object (and nothing else) with this exact structure:\n"
        "{\n"
        '  "payment_terms": "Advance",\n'
        '  "delivery_address": "",\n'
        '  "transport_extra": 0,\n'
        '  "sgst_percent": 9,\n'
        '  "cgst_percent": 9,\n'
        '  "notes": "",\n'
        '  "valid_until": null,\n'
        '  "line_items": [\n'
        '    {"hsn_code": "", "product_name": "", "length": null, "pcs": null, '
        '"quantity": 0, "uom": "ton", "unit_price": 0, "notes": ""}\n'
        "  ]\n"
        "}\n"
        "Valid uom values: 'ton' or 'kg'. Default to 'ton' if not specified. "
        "If a product is not found, include it with unit_price=0 and notes='Price not found — fill manually'. "
        "Never return anything outside the JSON object."
    )

    parts = [f"Customer enquiry: \n{lead.raw_text or '(no enquiry text)'}"]
    if lead.notes:
        parts.append(f"Lead notes:\n{lead.notes}")
    if entity_notes:
        parts.append(f"Customer/Broker notes:\n{entity_notes}")
    user_message = "\n\n".join(parts)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]

    response = together_client.chat.completions.create(
        model = TOGETHER_MODEL,
        messages = messages,
        tools = [PRICING_TOOL],
        tool_choice = "auto",
    )

    while True:
        message = response.choices[0].message

        if not message.tool_calls:
            break

        messages.append({
            'role': 'assistant',
            'content': message.content or '',
            'tool_calls': message.tool_calls,
        })

        for tool_call in message.tool_calls:
            args = json.loads(tool_call.function.arguments)
            result = lookup_pricing(**args)
            messages.append({
                'role': 'tool',
                'tool_call_id': tool_call.id,
                'content': json.dumps(result),
            })

        response = together_client.chat.completions.create(
            model=TOGETHER_MODEL,
            messages=messages,
            tools=[PRICING_TOOL],
            tool_choice='auto',
        )

    raw = response.choices[0].message.content or ''
    return json.loads(raw)
