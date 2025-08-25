# app/core/config.py
from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    """애플리케이션 환경 설정"""
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AI-Based Local Commerce Backend API"

    # 키는 비어 있어도 부팅되도록 기본값 제공
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GOOGLE_MAPS_API_KEY: str = os.getenv("GOOGLE_MAPS_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "AIzaSyCbRHVairhTvJLuctfxz7xhCS3eeGzjij8 ")
    NAVER_MAPS_API_KEY: str = os.getenv("NAVER_MAPS_API_KEY ", "22zPsBPvrlVHNjftWWWAJrA0QNvHj3XnsSpo3rnj")

    # CORS 허용 오리진 (쉼표 구분)
    CORS_ORIGINS: List[str] = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
