"""
Wrapper for together.ai LLM calls with tool use / function calling.
All views must call this service layer — never call together.ai directly.
"""
import os


TOGETHER_API_KEY = os.environ.get('TOGETHER_API_KEY', '')
TOGETHER_MODEL = os.environ.get('TOGETHER_MODEL', 'meta-llama/Llama-3.3-70B-Instruct-Turbo')


def generate_quotation_draft(lead_text: str, available_tools: list) -> dict:
    """
    Send lead text to the LLM and return a structured quotation draft.
    Stub — wire up together.ai client here in Phase 2.
    """
    raise NotImplementedError('LLM service not yet implemented — Phase 2 in progress.')
