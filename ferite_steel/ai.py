import os
from together import Together, TogetherError

together_client = Together(api_key=os.environ.get('TOGETHER_API_KEY', ''))


class LLMUnavailableError(Exception):
    """
    Raised whenever together.ai fails to serve a request. Carries a plain-language
    `user_message` safe to show to any user, and a `technical_detail` for admins/logs.
    Caught centrally by ferite_steel.middleware.LLMUnavailableMiddleware, which turns
    it into a friendly redirect instead of a 500 page.
    """
    def __init__(self, user_message, technical_detail=''):
        super().__init__(user_message)
        self.user_message = user_message
        self.technical_detail = technical_detail


def _record_llm_result(success: bool, error_message: str = ''):
    from django.utils import timezone
    from aegis.models import LLMApiStatus
    status, _ = LLMApiStatus.objects.get_or_create(pk=1)
    if success:
        status.last_success_at = timezone.now()
        status.consecutive_failures = 0
    else:
        status.last_failure_at = timezone.now()
        status.last_error_message = error_message[:2000]
        status.consecutive_failures += 1
    status.save()


def _handle_together_error(exc: TogetherError):
    status_code = getattr(exc, 'status_code', None)
    message = getattr(exc, 'message', str(exc))
    _record_llm_result(False, f'[{status_code}] {message}' if status_code else message)

    if status_code == 402:
        user_message = 'AI credits have run out — please inform your supervisor/admin so they can top up together.ai.'
    else:
        user_message = 'The AI service is temporarily unavailable. Please try again shortly, or contact your supervisor if this continues.'
    raise LLMUnavailableError(user_message, technical_detail=message) from exc


def chat_completion(**kwargs):
    """Use instead of together_client.chat.completions.create(**kwargs) directly —
    tracks API health and converts together.ai errors into LLMUnavailableError."""
    try:
        response = together_client.chat.completions.create(**kwargs)
    except TogetherError as exc:
        _handle_together_error(exc)
    _record_llm_result(True)
    return response


def create_embeddings(**kwargs):
    """Use instead of together_client.embeddings.create(**kwargs) directly —
    tracks API health and converts together.ai errors into LLMUnavailableError."""
    try:
        response = together_client.embeddings.create(**kwargs)
    except TogetherError as exc:
        _handle_together_error(exc)
    _record_llm_result(True)
    return response
