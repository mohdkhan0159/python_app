# app/settings.py
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    """
    Application settings that work in both local and Azure environments.
    
    Local (ENV=local):
    - Reads from .env file
    - Uses SQLite database
    - Uses local file storage
    
    Azure (ENV=production):
    - Reads from /mnt/secrets (Key Vault via CSI driver)
    - Uses Azure SQL database
    - Uses Azure Blob Storage
    """
    
    # ==========================================
    # ENVIRONMENT
    # ==========================================
    ENV: str = Field("local", env="ENV")
    
    # ==========================================
    # SESSION SECRET
    # ==========================================
    SESSION_SECRET: str = Field(
        "dev-secret-change-in-production-12345678901234567890",
        env="SESSION_SECRET"
    )
    
    # ==========================================
    # DATABASE
    # ==========================================
    # Local SQLite (default for development)
    DATABASE_URL: str = Field(
        "sqlite+aiosqlite:///./learning_platform.db",
        env="DATABASE_URL"
    )
    
    # Azure SQL (used when ENV=production)
    AZURE_SQL_CONNECTION_STRING: Optional[str] = Field(None, env="AZURE_SQL_CONNECTION_STRING")
    
    # ==========================================
    # AZURE STORAGE
    # ==========================================
    AZURE_STORAGE_CONNECTION_STRING: Optional[str] = Field(None, env="AZURE_STORAGE_CONNECTION_STRING")
    AZURE_STORAGE_ACCOUNT_NAME: Optional[str] = Field(None, env="AZURE_STORAGE_ACCOUNT_NAME")
    AZURE_STORAGE_ACCOUNT_KEY: Optional[str] = Field(None, env="AZURE_STORAGE_ACCOUNT_KEY")
    AZURE_STORAGE_CONTAINER: Optional[str] = Field("uploads", env="AZURE_STORAGE_CONTAINER")
    
    class Config:
        # Load from .env file in local development
        env_file = ".env"
        # Load from /mnt/secrets in Kubernetes (Key Vault CSI driver)
        secrets_dir = "/mnt/secrets"

# Initialize settings
try:
    settings = Settings()
except Exception as e:
    import sys
    print(f"FATAL: Settings load failed: {e}", file=sys.stderr)
    raise e
