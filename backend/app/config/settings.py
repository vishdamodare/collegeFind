from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    # Repo-root .env then .env.local (Neon writes .env.local). Real environment variables still win, which is
    # what keeps the test-suite pointed at the local test database.
    model_config = SettingsConfigDict(env_file=(str(_ROOT / ".env"), str(_ROOT / ".env.local")), extra="ignore")
    database_url: str = "postgresql+psycopg://localhost:5432/collegefind_dev"
    secret_key: str = ""  # must come from the environment; never hardcoded
    cors_origins: str = "http://localhost:3000,http://localhost:3100"
    # Dev only: also serve records still awaiting admin verification (always labelled in responses).
    serve_unverified: bool = False


    @field_validator("database_url")
    @classmethod
    def _psycopg3(cls, v: str) -> str:
        # Neon/Vercel hand out plain postgresql:// URLs; SQLAlchemy needs the psycopg3 driver named explicitly.
        for plain in ("postgresql://", "postgres://"):
            if v.startswith(plain):
                return "postgresql+psycopg://" + v[len(plain):]
        return v


settings = Settings()
