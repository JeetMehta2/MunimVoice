import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    PROJECT_NAME: str = "Munim - AI Business Partner"
    API_V1_STR: str = "/api"
    ENV: str = "development"
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        f"sqlite:///{DATA_DIR / 'munim.db'}"
    )
    
    # LLM Provider Configuration
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")  # gemini | anthropic | openai | mock
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Audio Storage Directory
    AUDIO_DIR: Path = DATA_DIR / "audio"
    
    # Hero Merchant Identity
    HERO_MERCHANT_ID: str = "merchant_sharma_chai"
    HERO_MERCHANT_NAME: str = "Sharma Chai & Snacks"
    HERO_CITY: str = "Jaipur"

settings = Settings()
settings.AUDIO_DIR.mkdir(parents=True, exist_ok=True)
