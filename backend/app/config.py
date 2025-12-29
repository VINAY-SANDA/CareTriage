"""
Application Configuration
Loads environment variables and provides centralized configuration.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
# Check multiple possible locations
possible_paths = [
    Path(__file__).parent.parent / '.env',  # backend/.env
    Path(__file__).parent.parent.parent / '.env',  # project/.env
]
for env_path in possible_paths:
    if env_path.exists():
        load_dotenv(env_path)
        break

class Settings:
    """Application settings loaded from environment variables."""
    
    # API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    
    # Paths - __file__ is in app/config.py, so parent.parent gets us to backend/
    BASE_DIR: Path = Path(__file__).parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    ICMR_DOCS_DIR: Path = DATA_DIR / "icmr_documents"
    TRAINING_DATA_DIR: Path = DATA_DIR / "training_data"
    VECTOR_STORE_DIR: Path = BASE_DIR / "app" / "knowledge_base" / "vector_store"
    MODELS_DIR: Path = BASE_DIR / "app" / "models"
    
    # Model Settings
    GEMINI_MODEL: str = "gemini-1.5-flash"
    EMBEDDING_MODEL: str = "models/embedding-001"
    
    # RAG Settings
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    TOP_K_RESULTS: int = 5
    
    # Risk Engine Settings
    RISK_THRESHOLD: float = 0.6
    
    # Server Settings
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required settings are present."""
        if not cls.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        return True

settings = Settings()
