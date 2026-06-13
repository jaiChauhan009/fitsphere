from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    DATABASE_URL: str
    SUPABASE_URL: str = ""
    SUPABASE_PUBLISHABLE_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    REDIS_URL: str = "redis://localhost:6379"
    FIREBASE_PROJECT_ID: str = ""
    FIREBASE_SERVICE_ACCOUNT_JSON: str = ""
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    USDA_API_KEY: str = ""
    SECRET_KEY: str = "change-this-in-production"
    APP_ENV: str = "development"
    CORS_ORIGINS: str = "https://fitsphere-1-sz2o.onrender.com"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"


settings = Settings()
