import secrets

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./scope_proxy.db"
    secret_key: str | None = None
    session_cookie_name: str = "scope_proxy_session"

    @property
    def secret_key_is_generated(self) -> bool:
        return self.secret_key is None


settings = Settings()
if settings.secret_key is None:
    settings.secret_key = secrets.token_urlsafe(32)
