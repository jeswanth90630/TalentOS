import os
from pydantic_settings import BaseSettings

class Settings:
    PROJECT_NAME: str = "TalentOS"
    PROJECT_VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./talentos.db")

settings = Settings()
