class RateLimitError(Exception):
    """API call limit breach exception handling"""
    pass


class RetryAttemptsFailed(Exception):
    """All retries failed on model generation calls"""
    pass


class MaximumContextLengthReached(Exception):
    """Maximum context length breach error"""
    pass