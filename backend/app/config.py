import secrets

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./scope_proxy.db"
    secret_key: str | None = None
    session_cookie_name: str = "scope_proxy_session"
    # Interval in seconds between automatic schema syncs. 0 (default) disables the background loop.
    # This is only the fallback default: a value set from the dashboard GUI (backend_config.
    # schema_sync_interval_seconds) takes precedence and can be changed without a restart.
    schema_sync_interval_seconds: int = 0

    request_log_retention_days: int = 30
    """How long request_logs rows are kept before opportunistic pruning removes them."""

    # Whether the session cookie requires HTTPS (Secure attribute). Default to True
    # since this app is meant to be deployed behind HTTPS; set to False only for
    # local HTTP development.
    session_cookie_secure: bool = True
    # Session cookie lifetime in seconds. None means a browser-session cookie
    # (no explicit expiry, matching Starlette's own default behavior).
    session_cookie_max_age: int | None = 14 * 24 * 60 * 60

    # Login brute-force protection (in-process, single-worker only; see
    # app/auth/rate_limiter.py). A key (IP address or email) is blocked once it
    # accumulates this many failed attempts within the window.
    login_rate_limit_max_attempts: int = 20
    login_rate_limit_window_seconds: float = 60.0

    # Timeout (in seconds) applied to requests forwarded to upstream backends.
    # Set to a larger value (or None to disable) if the upstream API is expected
    # to take longer than the default.
    proxy_timeout_seconds: float | None = 30.0

    # Comma-separated list of origins allowed to make cross-origin requests to the proxy.
    # Empty by default: CORS is disabled and every request (including preflight OPTIONS)
    # is handled by the normal auth flow, i.e. denied without a bearer token.
    cors_allowed_origins: str = ""

    @property
    def secret_key_is_generated(self) -> bool:
        return self.secret_key is None

    @property
    def cors_allowed_origins_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_allowed_origins.split(",")
            if origin.strip()
        ]


settings = Settings()
if settings.secret_key is None:
    settings.secret_key = secrets.token_urlsafe(32)
