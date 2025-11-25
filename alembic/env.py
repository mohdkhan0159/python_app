from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Import your models and settings
from app.models import Base
from app.settings import settings

# Alembic Config object
config = context.config

# Get database URL from settings
# Convert ODBC connection string to SQLAlchemy URL format
database_url = None

# Check if we're in production (Azure) or local
if settings.ENV == "production" and settings.AZURE_SQL_CONNECTION_STRING:
    # Azure SQL - convert ODBC format to SQLAlchemy URL
    odbc_string = settings.AZURE_SQL_CONNECTION_STRING
    
    # Parse ODBC connection string
    # Format: Server=tcp:server.database.windows.net,1433;Database=dbname;User ID=user;Password=pass;...
    import urllib.parse
    
    # Extract components from ODBC string
    parts = {}
    for part in odbc_string.split(';'):
        if '=' in part:
            key, value = part.split('=', 1)
            parts[key.strip()] = value.strip()
    
    # Build SQLAlchemy URL
    server = parts.get('Server', '').replace('tcp:', '').replace(',1433', '')
    database = parts.get('Database', '')
    username = parts.get('User ID', '')
    password = parts.get('Password', '')
    
    # URL encode the password
    password_encoded = urllib.parse.quote_plus(password)
    
    # Create SQLAlchemy URL with pyodbc driver
    database_url = f"mssql+pyodbc://{username}:{password_encoded}@{server}/{database}?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no"
else:
    # Local SQLite - convert async to sync
    database_url = settings.DATABASE_URL
    if '+aiosqlite' in database_url:
        database_url = database_url.replace('+aiosqlite', '')

if database_url:
    config.set_main_option('sqlalchemy.url', database_url)

# Interpret the config file for logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata for autogenerate support
target_metadata = Base.metadata


def run_migrations_offline():
    """Run migrations in 'offline' mode.
    
    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.
    
    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
