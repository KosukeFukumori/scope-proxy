import secrets

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./scope_proxy.db"
    secret_key: str | None = None
    session_cookie_name: str = "scope_proxy_session"
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
