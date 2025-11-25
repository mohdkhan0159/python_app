# app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.settings import settings
import urllib.parse

Base = declarative_base()

# ----------------------------------------------------------
# SELECT DATABASE BASED ON ENVIRONMENT
# ----------------------------------------------------------
def build_azure_sql_url():
    """
    Convert standard AZURE_SQL_CONNECTION_STRING into a valid
    SQLAlchemy async connection string using aioodbc.
    """

    raw = settings.AZURE_SQL_CONNECTION_STRING
    print(f"DEBUG: Raw connection string: '{raw}'")
    if not raw:
        return None

    # Azure SQL typical format:
    # Server=tcp:myserver.database.windows.net,1433;Database=mydb;User ID=user;Password=pass;
    # OR user may provide SQLAlchemy-style URL.

    if raw.startswith("mssql"):
        print("DEBUG: Raw string starts with mssql, returning as is.")
        # User already provided a SQLAlchemy URL
        return raw

    # Parse connection string into components
    # Handle both semicolon and ampersand separators
    parts = dict(
        item.split("=", 1)
        for item in raw.replace(";", "&").split("&")
        if "=" in item
    )

    # Extract connection parameters
    server = parts.get("Server") or parts.get("server")
    database = parts.get("Database") or parts.get("database") or parts.get("Initial Catalog")
    user = parts.get("User ID") or parts.get("uid") or parts.get("user")
    password = parts.get("Password") or parts.get("pwd")

    # Clean up server (remove tcp: prefix and port if present)
    if server:
        server = server.replace("tcp:", "").split(",")[0]

    print(f"DEBUG: Parsed - Server: {server}, Database: {database}, User: {user}, Password: {'***' if password else None}")

    if not (server and database and user and password):
        print("DEBUG: Missing required SQL auth parameters, falling back to odbc_connect")
        params = urllib.parse.quote_plus(raw)
        return f"mssql+aioodbc:///?odbc_connect={params}"

    # SQLAlchemy async driver (aioodbc)
    password_enc = urllib.parse.quote_plus(password)

    url = (
        f"mssql+aioodbc://{user}:{password_enc}@{server}/{database}"
        "?driver=ODBC+Driver+18+for+SQL+Server"
        "&Encrypt=yes"
        "&TrustServerCertificate=no"
    )
    print(f"DEBUG: Constructed User/Pass URL: {url}")
    return url


# ----------------------------------------------------------
# PICK DATABASE URL (LOCAL OR AZURE)
# ----------------------------------------------------------
if settings.ENV in ("production", "prod") and settings.AZURE_SQL_CONNECTION_STRING:
    print("Using Azure SQL")
    DATABASE_URL = build_azure_sql_url()
    print(f"DEBUG: Final DATABASE_URL: {DATABASE_URL}")
else:
    print("Using local SQLite")
    DATABASE_URL = settings.DATABASE_URL


# ----------------------------------------------------------
# SQLALCHEMY ENGINE (ASYNC)
# ----------------------------------------------------------
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    future=True,
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
