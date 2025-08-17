# app/core/config.py

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """애플리케이션 환경 설정"""
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AI-Based Local Commerce Backend API"
    OPENAI_API_KEY: str
    GOOGLE_MAPS_API_KEY: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()