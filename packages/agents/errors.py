from __future__ import annotations


class ProviderExecutionError(RuntimeError):
    def __init__(
        self,
        provider: str,
        message: str,
        *,
        status_code: int | None = None,
        mode: str | None = None,
    ):
        super().__init__(message)
        self.provider = provider
        self.status_code = status_code
        self.mode = mode


class ProviderAPIError(ProviderExecutionError):
    pass


class ProviderCLIError(ProviderExecutionError):
    pass


class ProviderRateLimitError(ProviderExecutionError):
    def __init__(
        self,
        provider: str,
        message: str,
        *,
        status_code: int | None = None,
        mode: str | None = None,
        reset_hint: str | None = None,
    ):
        super().__init__(provider=provider, message=message, status_code=status_code, mode=mode)
        self.reset_hint = reset_hint
