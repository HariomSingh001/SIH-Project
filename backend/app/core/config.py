"""
Application configuration using Pydantic Settings.
"""

from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables or defaults."""
    
    # App
    APP_NAME: str = "Pramaan AI API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    
    PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent.parent
    
    # Database
    DATABASE_URL: str = f"sqlite+aiosqlite:///{Path(__file__).resolve().parent.parent.parent.parent.as_posix()}/pramaan_ai.db"
    
    # CORS
    CORS_ORIGINS: list = ["*"]
    
    # AI Engine & Project Paths
    AI_ENGINE_PATH: str = str(Path(__file__).resolve().parent.parent.parent.parent / "ai_engine")
    DATA_PATH: str = str(Path(__file__).resolve().parent.parent.parent.parent / "data")
    OUTPUT_PATH: str = str(Path(__file__).resolve().parent.parent.parent.parent / "output")
    
    # Discrepancy Thresholds
    DISCREPANCY_WARNING_PERCENT: float = 15.0   # >=15% deficit = Warning
    DISCREPANCY_CRITICAL_PERCENT: float = 30.0   # >=30% deficit = Critical
    ACCEPTABLE_MARGIN_PERCENT: float = 10.0      # <=10% = Normal (acceptable)
    
    # Trust Score
    TRUST_SCORE_DECAY_PER_CRITICAL: float = 15.0
    TRUST_SCORE_DECAY_PER_WARNING: float = 5.0
    TRUST_SCORE_RECOVERY_PER_NORMAL: float = 2.0
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
