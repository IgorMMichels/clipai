from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Optional
import os
from dotenv import load_dotenv

# Load .env.local first (if exists), then .env as fallback
load_dotenv('.env.local')
load_dotenv('.env')


class Settings(BaseSettings):
    # App settings
    APP_NAME: str = "ClipAI"
    DEBUG: bool = True
    
    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent
    UPLOAD_DIR: Path = BASE_DIR.parent / "uploads"
    OUTPUT_DIR: Path = BASE_DIR.parent / "outputs"
    
    # API Keys
    GOOGLE_API_KEY: Optional[str] = None  # Gemini (primary)
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    HUGGINGFACE_TOKEN: Optional[str] = None  # For Pyannote
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./clipai.db"
    
    # Processing settings
    DEFAULT_ASPECT_RATIO: tuple = (9, 16)
    MAX_UPLOAD_SIZE_MB: int = 500
    
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        extra="allow"
    )


settings = Settings()

# Ensure directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
