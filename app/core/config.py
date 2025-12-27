from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)

    app_name: str = "FamilyHub"

    # IMPORTANT: set in .env
    secret_key: str = "CHANGE_ME"

    # DB (SQLite by default, mounted to ./data in Docker)
    database_url: str = "sqlite:///./data/familyhub.db"

    # Optional bootstrap admin. If set, app will ensure this admin exists on startup.
    bootstrap_admin_email: str | None = None
    bootstrap_admin_password: str | None = None

    # Session / security
    session_cookie: str = "fh_session"
    csrf_cookie: str = "fh_csrf"
    session_ttl_minutes: int = 60 * 24 * 14  # 14 days

    # App
    behind_proxy: bool = True  # set false if not using a reverse proxy


settings = Settings()
