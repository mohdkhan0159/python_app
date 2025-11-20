from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # --- CORE CONFIG ---
    SESSION_SECRET: str = "super-secret-local-key-123456789"
    ENV: str = "local"  

    # --- DATABASE CONFIG (SQLite locally, Azure SQL in cloud) ---
    DATABASE_URL: str = "sqlite+aiosqlite:///./learning_platform.db"
    AZURE_SQL_CONNECTION_STRING: str | None = None   # <-- FIXED

    # --- AZURE STORAGE ---
    AZURE_STORAGE_CONNECTION_STRING: str | None = None
    AZURE_STORAGE_ACCOUNT_NAME: str | None = None
    AZURE_STORAGE_ACCOUNT_KEY: str | None = None
    AZURE_STORAGE_CONTAINER: str | None = None
    AZURE_BLOB_CONTAINER: str | None = None

    # --- KEY VAULT ---
    KEY_VAULT_URL: str | None = None

    class Config:
        env_file = ".env"

settings = Settings()
