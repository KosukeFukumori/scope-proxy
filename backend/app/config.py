import secrets

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./scope_proxy.db"
    secret_key: str = secrets.token_urlsafe(32)
    session_cookie_name: str = "scope_proxy_session"


settings = Settings()
