from django.contrib import messages
from django.shortcuts import redirect

from .ai import LLMUnavailableError


class LLMUnavailableMiddleware:
    """
    Catches LLMUnavailableError raised from any view (LLM draft generation,
    RAG Q&A, quiz judging, note cleanup, credit risk assessment) and turns it
    into a friendly message + redirect instead of a 500 page.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if not isinstance(exception, LLMUnavailableError):
            return None
        messages.error(request, exception.user_message)
        return redirect(request.META.get('HTTP_REFERER') or 'dashboard')
