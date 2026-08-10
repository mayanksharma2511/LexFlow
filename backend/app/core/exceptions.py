class LLMServiceError(Exception):
    """Base exception for LLM service operational failures."""
    pass


class LLMRateLimitError(LLMServiceError):
    """Raised when LLM API rate limits are hit."""
    pass


class LLMQuotaExceededError(LLMServiceError):
    """Raised when LLM API provider quotas are exceeded."""
    pass


class LLMConnectionError(LLMServiceError):
    """Raised when connecting to LLM service fails."""
    pass
