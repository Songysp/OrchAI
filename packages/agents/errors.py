from __future__ import annotations


class ProviderAPIError(RuntimeError):
    def __init__(self, provider: str, message: str, *, status_code: int | None = None):
        super().__init__(message)
        self.provider = provider
        self.status_code = status_code


class ProviderRateLimitError(ProviderAPIError):
    def __init__(
        self,
        provider: str,
        message: str,
        *,
        status_code: int | None = None,
        reset_hint: str | None = None,
    ):
        super().__init__(provider=provider, message=message, status_code=status_code)
        self.reset_hint = reset_hint
